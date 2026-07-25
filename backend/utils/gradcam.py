"""
backend/utils/gradcam.py

Explainability heatmaps for both model types used in this project:

  • Keras (.keras / .h5)  →  Grad-CAM   (gradient-based, exact)
  • TFLite (.tflite)      →  Score-CAM  (activation-based, no gradients needed)

The two approaches are unified behind the same public API so route handlers
never need to care which model type they're dealing with.

────────────────────────────────────────────────────────────────────────────
Keras usage (eye disease model)
────────────────────────────────────────────────────────────────────────────
from backend.utils.gradcam import generate_gradcam_overlay

overlay_b64, heatmap_b64 = generate_gradcam_overlay(
    model=loaded_keras_model,
    img_path="uploads/retina_scan.jpg",
    class_index=predicted_index,
)

────────────────────────────────────────────────────────────────────────────
TFLite usage (skin disease model)
────────────────────────────────────────────────────────────────────────────
from backend.utils.gradcam import generate_tflite_scorecam_overlay

overlay_b64, heatmap_b64 = generate_tflite_scorecam_overlay(
    tflite_path="models/resnet50_models/skin_model.tflite",
    img_path="uploads/skin_lesion.jpg",
    class_index=predicted_index,
)

────────────────────────────────────────────────────────────────────────────
Unified convenience wrapper (handles both automatically)
────────────────────────────────────────────────────────────────────────────
from backend.utils.gradcam import predict_with_gradcam

result = predict_with_gradcam(
    model=keras_model_or_tflite_interpreter,
    img_path="uploads/any_image.jpg",
    class_names=CLASS_NAMES,
    tflite_path="models/resnet50_models/skin_model.tflite",  # only for TFLite
)

Both return values are base64-encoded PNG strings ready to embed in a JSON
response:  "data:image/png;base64,<string>"
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Optional

import cv2
import numpy as np
from PIL import Image

try:
    import tensorflow as tf
    from tensorflow.keras.models import Model

    _TF_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    tf = None  # type: ignore[assignment]
    Model = object  # type: ignore[assignment,misc]
    _TF_AVAILABLE = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_last_conv_layer(model: Model) -> str:
    """
    Walk the model layers in reverse and return the name of the last
    Conv2D (or Depthwise/Separable Conv) layer.

    For ResNet50 this is reliably 'conv5_block3_out' (the final residual
    addition after the last conv block), but we discover it dynamically so
    the same utility works for any CNN backbone.
    """
    for layer in reversed(model.layers):
        if isinstance(
            layer,
            (
                tf.keras.layers.Conv2D,
                tf.keras.layers.DepthwiseConv2D,
                tf.keras.layers.SeparableConv2D,
                # ResNet uses this as the residual merge point — it has
                # spatial dimensions and rich feature maps.
                tf.keras.layers.Add,
            ),
        ):
            # Skip Add layers that immediately precede the GlobalAvgPool;
            # we want a layer that still has (batch, H, W, C) shape.
            if len(layer.output.shape) == 4:
                logger.debug("Grad-CAM target layer: %s", layer.name)
                return layer.name

    raise ValueError(
        "Could not find a suitable convolutional layer in the model. "
        "Pass `last_conv_layer_name` explicitly."
    )


def _preprocess_image(
    img_path: str, target_size: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray]:
    """
    Load, resize, and preprocess an image using ResNet50's preprocess_input
    (ImageNet mean subtraction) — identical to what predict_disease_type_routes.py  # noqa: E501
    does, so the heatmap is computed on the exact same tensor the model saw.

    Returns
    -------
    img_array   : float32 array of shape (1, H, W, 3), ResNet50-normalised
    original_img: uint8 array of shape (H, W, 3) for overlay blending
    """
    img = (
        Image.open(img_path)
        .convert("RGB")
        .resize((target_size[1], target_size[0]))
    )
    original_img = np.array(img, dtype=np.uint8)  # (H, W, 3)

    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)  # (1, H, W, 3)
    img_array = tf.keras.applications.resnet50.preprocess_input(img_array)
    return img_array, original_img


def _compute_gradcam_heatmap(
    model: Model,
    img_array: np.ndarray,
    class_index: int,
    last_conv_layer_name: str,
) -> np.ndarray:
    """
    Core Grad-CAM computation.

    1. Build a sub-model that outputs (conv_activations, final_predictions).
    2. Forward-pass with GradientTape to record activations and gradients.
    3. Pool gradients spatially → weight each activation channel.
    4. ReLU + normalise → heatmap in [0, 1].

    Parameters
    ----------
    model               : compiled Keras model (eye or skin)
    img_array           : preprocessed input, shape (1, H, W, 3)
    class_index         : index of the predicted class (from np.argmax)
    last_conv_layer_name: name of the convolutional layer to hook

    Returns
    -------
    heatmap : float32 array of shape (h, w), values in [0, 1]
    """
    # Sub-model: inputs → [conv_output, predictions]
    grad_model = Model(
        inputs=model.inputs,
        outputs=[
            model.get_layer(last_conv_layer_name).output,
            model.output,
        ],
    )

    with tf.GradientTape() as tape:
        inputs = tf.cast(img_array, tf.float32)
        conv_outputs, predictions = grad_model(inputs)
        # Score for the predicted class only
        loss = predictions[:, class_index]

    # Gradients of class score w.r.t. conv feature maps
    grads = tape.gradient(loss, conv_outputs)  # (1, h, w, C)

    # Global-average-pool the gradients over the spatial axes → (1, 1, 1, C)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))  # (C,)

    # Weight each activation channel by its pooled gradient
    conv_outputs = conv_outputs[0]  # (h, w, C)
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]  # (h, w, 1)
    heatmap = tf.squeeze(heatmap)  # (h, w)

    # ReLU: keep only positive influences on the class score
    heatmap = tf.nn.relu(heatmap)

    # Normalise to [0, 1]
    heatmap = heatmap.numpy()
    max_val = heatmap.max()
    if max_val > 0:
        heatmap /= max_val

    return heatmap.astype(np.float32)


def _heatmap_to_colormap(
    heatmap: np.ndarray, target_hw: tuple[int, int]
) -> np.ndarray:
    """
    Resize the raw heatmap to target (H, W) and apply the COLORMAP_JET
    colour palette, returning a uint8 RGB array of shape (H, W, 3).
    """
    h, w = target_hw
    # cv2 resize needs (width, height)
    resized = cv2.resize(heatmap, (w, h))
    # Scale to uint8
    scaled = np.uint8(255 * resized)
    # Apply colour map (returns BGR)
    coloured_bgr = cv2.applyColorMap(scaled, cv2.COLORMAP_JET)
    # Convert to RGB
    coloured_rgb = cv2.cvtColor(coloured_bgr, cv2.COLOR_BGR2RGB)
    return coloured_rgb


def _blend_overlay(
    original_img: np.ndarray,
    coloured_heatmap: np.ndarray,
    alpha: float = 0.45,
) -> np.ndarray:
    """
    Alpha-blend the heatmap over the original image.

    overlay = alpha * heatmap + (1 - alpha) * original
    """
    original_f = original_img.astype(np.float32)
    heatmap_f = coloured_heatmap.astype(np.float32)
    blended = alpha * heatmap_f + (1.0 - alpha) * original_f
    return np.clip(blended, 0, 255).astype(np.uint8)


def _array_to_base64_png(arr: np.ndarray) -> str:
    """
    Encode a uint8 RGB numpy array as a base64 PNG data URI.
    """
    pil_img = Image.fromarray(arr)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


# ---------------------------------------------------------------------------
# TFLite Score-CAM  (skin_model.tflite)
# ---------------------------------------------------------------------------
#
# Why Score-CAM instead of Grad-CAM for TFLite?
# ──────────────────────────────────────────────
# TFLite's Interpreter exposes a flat tensor list, not a differentiable
# computation graph, so tf.GradientTape cannot hook into it.
#
# Score-CAM sidesteps gradients entirely:
#   1. Run a forward pass → get the raw activations of an intermediate tensor
#      (the last spatial feature map, identified by shape heuristic).
#   2. For each activation channel:
#        a. Upsample the channel mask to input resolution.
#        b. Normalise the mask to [0, 1].
#        c. Multiply the mask element-wise with the input image.
#        d. Run another forward pass on the masked image.
#        e. Record the class score — this is the channel's "contribution".
#   3. Weight each channel's activation map by its contribution score.
#   4. Sum → ReLU → normalise → same heatmap format as Grad-CAM.
#
# Trade-off: O(C) forward passes where C = number of channels in the chosen
# tensor.  We cap at MAX_SCORECAM_CHANNELS (default 32) by selecting the
# top-variance channels, keeping latency acceptable on CPU.

MAX_SCORECAM_CHANNELS = 32  # increase for higher fidelity at the cost of speed


def _get_tflite_interpreter(tflite_path: str) -> "tf.lite.Interpreter":
    """
    Load a fresh TFLite interpreter for Score-CAM.

    XNNPACK is explicitly disabled because it optimises away intermediate
    tensor buffers, making get_tensor() on feature maps return null data.
    Without XNNPACK every tensor stays in memory and is readable after invoke.
    """
    interpreter = tf.lite.Interpreter(
        model_path=tflite_path,
        experimental_delegates=[],  # disable XNNPACK / any hardware delegate
        num_threads=1,
    )
    interpreter.allocate_tensors()
    return interpreter


def _find_tflite_feature_tensor(
    interpreter: "tf.lite.Interpreter",
) -> int:
    """
    Find a tensor index that has live runtime data after invoke().
    We do a dummy forward pass first, then check which 4-D spatial
    tensors actually contain non-null data.
    """
    import numpy as np

    # Dummy forward pass so runtime buffers are populated
    input_details = interpreter.get_input_details()
    interpreter.get_output_details()
    dummy = np.zeros(input_details[0]["shape"], dtype=np.float32)
    interpreter.allocate_tensors()
    interpreter.set_tensor(input_details[0]["index"], dummy)
    interpreter.invoke()

    candidate = None
    for detail in interpreter.get_tensor_details():
        shape = detail["shape"]
        if len(shape) != 4:
            continue
        if shape[1] <= 1 or shape[2] <= 1:
            continue
        # Try reading the tensor — skip if null (weights/constants)
        try:
            data = interpreter.get_tensor(detail["index"])
            if data is not None:
                candidate = detail["index"]
        except Exception:
            continue

    if candidate is None:
        raise ValueError(
            "Could not find a live spatial feature tensor in the TFLite model."
        )

    logger.debug("Score-CAM feature tensor index: %d", candidate)
    return candidate


def _tflite_infer(
    interpreter: "tf.lite.Interpreter",
    img_array: np.ndarray,
) -> np.ndarray:
    """
    Run a single forward pass and return the output tensor as a float32 array.
    img_array must be shape (1, H, W, 3), dtype float32.

    allocate_tensors() is called before every invoke — required after each
    set_tensor call on interpreters that are reused across multiple inferences.
    """
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(
        input_details[0]["index"], img_array.astype(np.float32)
    )
    interpreter.invoke()
    return interpreter.get_tensor(
        output_details[0]["index"]
    )  # (1, num_classes)


def _tflite_infer_with_feature(
    interpreter: "tf.lite.Interpreter",
    img_array: np.ndarray,
    feature_tensor_index: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Forward pass that also captures the intermediate feature tensor.

    Returns
    -------
    feature_map : float32 array of shape (H_feat, W_feat, C)
    predictions : float32 array of shape (num_classes,)
    """
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.allocate_tensors()
    interpreter.set_tensor(
        input_details[0]["index"], img_array.astype(np.float32)
    )
    interpreter.invoke()

    feature_map = interpreter.get_tensor(feature_tensor_index)[
        0
    ]  # drop batch dim
    predictions = interpreter.get_tensor(output_details[0]["index"])[0]
    return feature_map, predictions


def _compute_scorecam_heatmap(
    interpreter: "tf.lite.Interpreter",
    img_array: np.ndarray,
    class_index: int,
    feature_tensor_index: int,
    max_channels: int = MAX_SCORECAM_CHANNELS,
) -> np.ndarray:
    """
    Score-CAM heatmap computation for a TFLite interpreter.

    Parameters
    ----------
    interpreter          : Allocated TFLite Interpreter.
    img_array            : Preprocessed input, shape (1, H, W, 3), float32 [0,1].  # noqa: E501
    class_index          : Predicted class index.
    feature_tensor_index : Index of the intermediate spatial tensor to use.
    max_channels         : Cap on number of channels to probe (speed vs fidelity).  # noqa: E501

    Returns
    -------
    heatmap : float32 array of shape (H, W), values in [0, 1].
    """
    input_h = img_array.shape[1]
    input_w = img_array.shape[2]

    # ── Step 1: single forward pass to get feature maps ────────────────────
    feature_map, _ = _tflite_infer_with_feature(
        interpreter, img_array, feature_tensor_index
    )
    # feature_map shape: (h_feat, w_feat, C)
    h_feat, w_feat, num_channels = feature_map.shape

    # ── Step 2: select top-variance channels to stay within budget ──────────
    channel_variances = feature_map.var(axis=(0, 1))  # (C,)
    if num_channels > max_channels:
        top_indices = np.argsort(channel_variances)[-max_channels:]
    else:
        top_indices = np.arange(num_channels)

    # ── Step 3: Score-CAM loop ──────────────────────────────────────────────
    cam_accumulator = np.zeros((h_feat, w_feat), dtype=np.float32)

    for ch_idx in top_indices:
        # (a) Extract and upsample this channel's activation mask
        channel_act = feature_map[:, :, ch_idx]  # (h_feat, w_feat)
        mask_resized = cv2.resize(channel_act, (input_w, input_h))  # (H, W)

        # (b) Normalise mask to [0, 1]
        m_min, m_max = mask_resized.min(), mask_resized.max()
        if m_max - m_min < 1e-8:
            continue  # flat channel — skip
        mask_norm = (mask_resized - m_min) / (m_max - m_min)  # (H, W)

        # (c) Apply mask to input image
        mask_3c = mask_norm[:, :, np.newaxis]  # (H, W, 1)
        masked_img = img_array * mask_3c  # (1, H, W, 3)

        # (d) Forward pass on masked image
        masked_preds = _tflite_infer(
            interpreter, masked_img
        )  # (1, num_classes)
        score = float(masked_preds[0, class_index])

        # (e) Accumulate: weight activation map by the class score
        cam_accumulator += score * channel_act

    # ── Step 4: ReLU + normalise ────────────────────────────────────────────
    cam_accumulator = np.maximum(cam_accumulator, 0)
    max_val = cam_accumulator.max()
    if max_val > 0:
        cam_accumulator /= max_val

    return cam_accumulator.astype(np.float32)


def generate_tflite_scorecam_overlay(
    tflite_path: str,
    img_path: str,
    class_index: int,
    target_size: tuple[int, int] = (224, 224),
    feature_tensor_index: Optional[int] = None,
    heatmap_alpha: float = 0.45,
    max_channels: int = MAX_SCORECAM_CHANNELS,
) -> tuple[str, str]:
    """
    Generate a Score-CAM explanation for a TFLite model prediction.

    Parameters
    ----------
    tflite_path          : Filesystem path to the .tflite model file.
    img_path             : Filesystem path to the uploaded image.
    class_index          : Predicted class index (from a prior inference call).
    target_size          : (H, W) the model expects; default (224, 224).
    feature_tensor_index : Index of the intermediate tensor to use as the
                           feature map.  Auto-detected when None.
    heatmap_alpha        : Blend strength of the heatmap overlay (0–1).
    max_channels         : Max activation channels to probe (speed vs fidelity).  # noqa: E501

    Returns
    -------
    overlay_b64  : base64 PNG — original image with heatmap blended on top.
    heatmap_b64  : base64 PNG — raw coloured heatmap.
    """
    interpreter = _get_tflite_interpreter(tflite_path)

    if feature_tensor_index is None:
        feature_tensor_index = _find_tflite_feature_tensor(interpreter)

    img_array, original_img = _preprocess_image(img_path, target_size)

    heatmap = _compute_scorecam_heatmap(
        interpreter, img_array, class_index, feature_tensor_index, max_channels
    )

    h, w = original_img.shape[:2]
    coloured_heatmap = _heatmap_to_colormap(heatmap, target_hw=(h, w))
    overlay = _blend_overlay(
        original_img, coloured_heatmap, alpha=heatmap_alpha
    )

    overlay_b64 = _array_to_base64_png(overlay)
    heatmap_b64 = _array_to_base64_png(coloured_heatmap)

    logger.info(
        "Score-CAM generated | tensor_idx=%d | class_index=%d | img=%s",
        feature_tensor_index,
        class_index,
        img_path,
    )

    return overlay_b64, heatmap_b64


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_gradcam_overlay(
    model: Model,
    img_path: str,
    class_index: int,
    target_size: tuple[int, int] = (224, 224),
    last_conv_layer_name: Optional[str] = None,
    heatmap_alpha: float = 0.45,
) -> tuple[str, str]:
    """
    Generate a Grad-CAM explanation for a single prediction.

    Parameters
    ----------
    model                : Loaded Keras model (eye disease or skin disease).
    img_path             : Filesystem path to the uploaded image.
    class_index          : Integer class index returned by np.argmax(predictions).  # noqa: E501
    target_size          : (H, W) — must match what the model expects (default 224×224).  # noqa: E501
    last_conv_layer_name : Name of the conv layer to hook into.  If None, the
                           last Conv2D/Add layer is discovered automatically.
    heatmap_alpha        : Blending weight of the heatmap (0 = invisible, 1 = opaque).  # noqa: E501
                           0.45 gives a legible overlay without washing out anatomy.  # noqa: E501

    Returns
    -------
    overlay_b64  : base64 PNG — original image with heatmap blended on top.
    heatmap_b64  : base64 PNG — raw coloured heatmap (useful for side-by-side display).  # noqa: E501

    Raises
    ------
    ValueError   : if no suitable conv layer is found and none is supplied.
    Exception    : propagates any image-loading or TF errors so the caller
                   can wrap in try/except and return a graceful API error.
    """
    # 1. Resolve which conv layer to hook
    if last_conv_layer_name is None:
        last_conv_layer_name = _find_last_conv_layer(model)

    # 2. Load + preprocess
    img_array, original_img = _preprocess_image(img_path, target_size)

    # 3. Compute raw heatmap
    heatmap = _compute_gradcam_heatmap(
        model, img_array, class_index, last_conv_layer_name
    )

    # 4. Colourise + resize to original image dimensions
    h, w = original_img.shape[:2]
    coloured_heatmap = _heatmap_to_colormap(heatmap, target_hw=(h, w))

    # 5. Blend over original
    overlay = _blend_overlay(
        original_img, coloured_heatmap, alpha=heatmap_alpha
    )

    # 6. Encode both as base64 PNG data URIs
    overlay_b64 = _array_to_base64_png(overlay)
    heatmap_b64 = _array_to_base64_png(coloured_heatmap)

    logger.info(
        "Grad-CAM generated | layer=%s | class_index=%d | img=%s",
        last_conv_layer_name,
        class_index,
        img_path,
    )

    return overlay_b64, heatmap_b64


# ---------------------------------------------------------------------------
# Convenience wrapper — drop-in alongside predict_disease()
# ---------------------------------------------------------------------------


def predict_with_gradcam(
    model,
    img_path: str,
    class_names: list[str],
    target_size: tuple[int, int] = (224, 224),
    confidence_threshold: float = 0.65,
    # Keras-specific
    last_conv_layer_name: Optional[str] = None,
    # TFLite-specific
    tflite_path: Optional[str] = None,
    feature_tensor_index: Optional[int] = None,
    max_scorecam_channels: int = MAX_SCORECAM_CHANNELS,
    # Shared
    heatmap_alpha: float = 0.45,
) -> dict:
    """
    Unified inference + explainability wrapper for both model types.

    Automatically detects whether ``model`` is a Keras Model or a TFLite
    Interpreter and routes to Grad-CAM or Score-CAM accordingly.

    Parameters
    ----------
    model                : Keras Model  OR  tf.lite.Interpreter.
    img_path             : Path to the uploaded image.
    class_names          : Ordered list of class labels.
    target_size          : Model input (H, W); default (224, 224).
    confidence_threshold : Predictions below this are flagged "uncertain".
    last_conv_layer_name : [Keras only] Conv layer to hook; auto-detected when None.  # noqa: E501
    tflite_path          : [TFLite only] Path to the .tflite file — needed to
                           reload the interpreter for Score-CAM's extra passes.
    feature_tensor_index : [TFLite only] Intermediate tensor index; auto-detected.  # noqa: E501
    max_scorecam_channels: [TFLite only] Channel budget for Score-CAM.
    heatmap_alpha        : Heatmap blend strength (0–1).

    Returns
    -------
    dict with keys:
        status           – "success" | "uncertain" | "error"
        disease          – predicted class label (or None)
        confidence       – float in [0, 1]
        message          – human-readable status string
        gradcam_overlay  – base64 PNG data URI (overlay) or None on error
        gradcam_heatmap  – base64 PNG data URI (raw heatmap) or None on error
        explanation_method – "grad-cam" | "score-cam" | None
    """
    gradcam_overlay = None
    gradcam_heatmap = None
    explanation_method = None

    # ── Detect model type ───────────────────────────────────────────────────
    is_tflite = isinstance(model, tf.lite.Interpreter)

    try:
        img_array, _ = _preprocess_image(img_path, target_size)

        # ── Inference ───────────────────────────────────────────────────────
        if is_tflite:
            predictions = _tflite_infer(model, img_array)  # (1, C)
            predictions = predictions[0]  # (C,)
        else:
            predictions = model.predict(img_array)[0]  # (C,)

        confidence = float(np.max(predictions))
        predicted_index = int(np.argmax(predictions))

        # ── Explainability ──────────────────────────────────────────────────
        # Generated even for uncertain predictions so the UI can visualise
        # why the model lacked confidence.
        try:
            if is_tflite:
                if tflite_path is None:
                    raise ValueError(
                        "tflite_path must be supplied for Score-CAM on a TFLite model. "  # noqa: E501
                        "Example: predict_with_gradcam(model=interpreter, "
                        "tflite_path='models/resnet50_models/skin_model.tflite', ...)"  # noqa: E501
                    )
                gradcam_overlay, gradcam_heatmap = (
                    generate_tflite_scorecam_overlay(
                        tflite_path=tflite_path,
                        img_path=img_path,
                        class_index=predicted_index,
                        target_size=target_size,
                        feature_tensor_index=feature_tensor_index,
                        heatmap_alpha=heatmap_alpha,
                        max_channels=max_scorecam_channels,
                    )
                )
                explanation_method = "score-cam"
            else:
                gradcam_overlay, gradcam_heatmap = generate_gradcam_overlay(
                    model=model,
                    img_path=img_path,
                    class_index=predicted_index,
                    target_size=target_size,
                    last_conv_layer_name=last_conv_layer_name,
                    heatmap_alpha=heatmap_alpha,
                )
                explanation_method = "grad-cam"

        except Exception as cam_err:
            # Explainability failure must NOT kill the prediction response
            logger.warning(
                "Heatmap generation failed (%s): %s",
                explanation_method,
                cam_err,
            )

        # ── Uncertainty gate ────────────────────────────────────────────────
        if confidence < confidence_threshold:
            return {
                "status": "uncertain",
                "disease": None,
                "confidence": round(confidence, 4),
                "message": (
                    "Insufficient data to predict reliably. "
                    "Please provide a clearer image or more information."
                ),
                "gradcam_overlay": gradcam_overlay,
                "gradcam_heatmap": gradcam_heatmap,
                "explanation_method": explanation_method,
            }

        predicted_disease = class_names[predicted_index]

        return {
            "status": "success",
            "disease": predicted_disease,
            "confidence": round(confidence, 4),
            "message": "Prediction generated successfully.",
            "gradcam_overlay": gradcam_overlay,
            "gradcam_heatmap": gradcam_heatmap,
            "explanation_method": explanation_method,
        }

    except Exception as e:
        logger.error("predict_with_gradcam failed: %s", e)
        return {
            "status": "error",
            "disease": None,
            "confidence": 0.0,
            "message": f"Prediction failed: {str(e)}",
            "gradcam_overlay": None,
            "gradcam_heatmap": None,
            "explanation_method": None,
        }
