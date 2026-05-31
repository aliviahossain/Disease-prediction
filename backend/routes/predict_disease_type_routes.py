# Suppress numpy warnings
import os
import tempfile  # NEW: needed to save upload to disk for Grad-CAM
import warnings

import numpy as np
import tensorflow as tf
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from PIL import Image

from backend.services.history_service import save_history
from backend.utils.gradcam import generate_gradcam_overlay  # NEW
from backend.utils.gradcam import generate_tflite_scorecam_overlay

# Import TensorFlow models


warnings.filterwarnings("ignore", category=FutureWarning, message=".*np.object.*")
warnings.filterwarnings(
    "ignore", message=".*tf.lite.Interpreter is deprecated.*", category=UserWarning
)
warnings.filterwarnings("ignore", message=".*np.object.*", category=FutureWarning)

# Suppress TensorFlow logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

predict_disease_type_bp = Blueprint("disease-type", __name__)

# CONFIG
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add any new disease types models here
MODEL_CONFIG = {
    "eyes": {
        "format": "keras",
        "path": os.path.join(
            BACKEND_DIR, "models", "resnet50_models", "eye_disease_resnet50_fp16.keras"
        ),
        "class_names": [
            "Cataract",
            "Diabetic Retinopathy",
            "Glaucoma",
            "Normal",
        ],
        "img_size": (224, 224),
    },
    "skin": {
        "format": "tflite",
        "path": os.path.join(
            BACKEND_DIR, "models", "resnet50_models", "skin_model.tflite"
        ),
        "class_names": [
            "Atopic Dermatitis",
            "Basal Cell Carcinoma",
            "Benign Keratosis-like Lesions",
            "Eczema",
            "Melanocytic Nevi",
            "Melanoma",
            "Psoriasis",
            "Seborrheic Keratoses and other Benign Tumors",
            "Tinea Ringworm Candidiasis and other Fungal Infections",
            "Warts Molluscum and other Viral Infections",
        ],
        "img_size": (224, 224),
        "dtype": "float32",
    },
}

# Model caches
KERAS_MODEL_CACHE = {}
TFLITE_MODEL_CACHE = {}

# Confidence threshold for eliminating low-confidence predictions (can be adjusted or made dynamic)
CONFIDENCE_THRESHOLD = 0.60

# loads keras model in the KERAS_MODEL_CACHE (for eye disease prediction)
def load_keras_model(model_type):
    if model_type not in KERAS_MODEL_CACHE:
        path = MODEL_CONFIG[model_type]["path"]
        print(f"Loading Keras model: {model_type}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found: {path}")

        KERAS_MODEL_CACHE[model_type] = tf.keras.models.load_model(path, compile=False)
    return KERAS_MODEL_CACHE[model_type]


# loads tflite model in the TFLITE_MODEL_CACHE(for skin disease prediction)
def load_tflite_model(model_type):
    if model_type not in TFLITE_MODEL_CACHE:
        path = MODEL_CONFIG[model_type]["path"]
        print(f"Loading TFLite model: {model_type}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found: {path}")

        interpreter = tf.lite.Interpreter(model_path=path)
        interpreter.allocate_tensors()

        TFLITE_MODEL_CACHE[model_type] = {
            "interpreter": interpreter,
            "input_details": interpreter.get_input_details(),
            "output_details": interpreter.get_output_details(),
        }
    return TFLITE_MODEL_CACHE[model_type]


# preprocesses image for model input
def preprocess_image(file, model_type):
    config = MODEL_CONFIG[model_type]
    size = config["img_size"]

    img = Image.open(file).convert("RGB")
    img = img.resize(size)

    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)

    # ResNet-style normalization (works for both models)
    img_array = tf.keras.applications.resnet50.preprocess_input(img_array)
    return img_array


# runs and predicts output for keras model
def run_keras_inference(model_type, img_array):
    model = load_keras_model(model_type)
    preds = model.predict(img_array)[0]
    return preds


# runs and predicts output for tflite model
def run_tflite_inference(model_type, img_array):
    model_data = load_tflite_model(model_type)
    interpreter = model_data["interpreter"]
    input_details = model_data["input_details"]
    output_details = model_data["output_details"]

    # Handle INT8 vs float model
    if MODEL_CONFIG[model_type].get("dtype") == "uint8":
        img_array = img_array.astype(np.uint8)

    interpreter.set_tensor(input_details[0]["index"], img_array)
    interpreter.invoke()

    preds = interpreter.get_tensor(output_details[0]["index"])[0]
    return preds


# Magic bytes for the image formats the models accept.
# The check uses the first 12 bytes of the upload, which is sufficient
# to distinguish JPEG (FF D8 FF), PNG (89 50 4E 47), and WebP (52 49 46 46 ... 57 45 42 50).
_IMAGE_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"RIFF": "image/webp",  # full WebP header checked below
}
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _validate_image_magic(stream) -> bool:
    """Return True only if the leading bytes identify a supported image format."""
    header = stream.read(12)
    stream.seek(0)
    if not header:
        return False
    if header[:3] in _IMAGE_MAGIC or header[:4] in _IMAGE_MAGIC:
        return True
    # WebP: bytes 0-3 = 'RIFF', bytes 8-11 = 'WEBP'
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return True
    return False


#  Main prediction route
@predict_disease_type_bp.route("/predict", methods=["POST"])
@login_required
def predict():
    # Accept file as "image" or "file"
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files["image"]

    # Reject uploads that exceed the size limit before reading the full stream.
    image_file.stream.seek(0, 2)
    file_size = image_file.stream.tell()
    image_file.stream.seek(0)
    if file_size > _MAX_UPLOAD_BYTES:
        return jsonify({"error": "File size exceeds the 10 MB limit."}), 400

    # Validate the file magic bytes before using the filename extension.
    # Extension-only checks are trivially bypassed by renaming any file to .jpg.
    if not _validate_image_magic(image_file.stream):
        return jsonify({"error": "Uploaded file is not a recognised image (JPEG, PNG, or WebP)."}), 400

    # Accept type from form or JSON
    model_type = (
        request.form.get("type")
        or (request.json.get("type") if request.is_json else None)
        or "eyes"
    ).lower()

    print("model_type: ", model_type)

    if model_type not in MODEL_CONFIG:
        return (
            jsonify(
                {
                    "error": f"Invalid type '{model_type}'. Use one of: {list(MODEL_CONFIG.keys())}"
                }
            ),
            400,
        )

    print(model_type not in MODEL_CONFIG)

    try:
        # NEW: Save the upload to a temp file on disk so Grad-CAM can read
        # it by path (PIL.open from a stream can only be read once).
        suffix = os.path.splitext(image_file.filename or ".jpg")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            image_file.save(tmp)
            tmp_path = tmp.name

        try:
            # 1. Preprocess image
            img_array = preprocess_image(tmp_path, model_type)

            # 2. Run inference model to get predictions
            if MODEL_CONFIG[model_type]["format"] == "keras":
                preds = run_keras_inference(model_type, img_array)
            else:
                preds = run_tflite_inference(model_type, img_array)

            # 3. Get predicted class and confidence
            idx = int(np.argmax(preds))
            confidence = float(preds[idx])
            predicted_class = MODEL_CONFIG[model_type]["class_names"][idx]


            print(
                f"Prediction: {predicted_class}, "
                f"Confidence: {confidence:.4f}"
            )

            if confidence < CONFIDENCE_THRESHOLD:
                return jsonify({
                    "error": (
                        f"The uploaded image does not appear to be a valid "
                        f"{model_type} disease image. "
                        "Please upload a clear medical image."
                    ),
                    "confidence": round(confidence * 100, 2)
                }), 400

            # 4. NEW: Generate Grad-CAM / Score-CAM heatmap
            gradcam_overlay = None
            gradcam_heatmap = None
            explanation_method = None

            try:
                config = MODEL_CONFIG[model_type]

                if config["format"] == "keras":
                    # Eye model → Grad-CAM using the cached Keras model
                    keras_model = load_keras_model(model_type)
                    gradcam_overlay, gradcam_heatmap = generate_gradcam_overlay(
                        model=keras_model,
                        img_path=tmp_path,
                        class_index=idx,
                        target_size=config["img_size"],
                    )
                    explanation_method = "grad-cam"

                else:
                    # Skin model → Score-CAM using the .tflite file path
                    gradcam_overlay, gradcam_heatmap = generate_tflite_scorecam_overlay(
                        tflite_path=config["path"],
                        img_path=tmp_path,
                        class_index=idx,
                        target_size=config["img_size"],
                    )
                    explanation_method = "score-cam"

            except Exception as cam_err:
                import traceback

                print(f"[Grad-CAM] Warning: heatmap generation failed: {cam_err}")
                traceback.print_exc()

        finally:
            # Always clean up the temp file
            os.unlink(tmp_path)

        # 5. Persist prediction history (unchanged)
        save_history(
            user_id=current_user.id if current_user.is_authenticated else None,
            prediction_type=model_type,
            disease=predicted_class,
            inputs={
                "type": model_type,
                "image_filename": getattr(image_file, "filename", None),
            },
            results={
                "prediction": predicted_class,
                "confidence_pct": round(confidence * 100, 2),
            },
            probability=confidence,
        )

        # 6. Return prediction + heatmap (gradcam fields are None if generation failed)
        return (
            jsonify(
                {
                    "prediction": predicted_class,
                    "confidence": round(confidence * 100, 2),
                    "type": model_type,
                    "gradcam_overlay": gradcam_overlay,  # NEW: base64 PNG, image + heatmap blended
                    "gradcam_heatmap": gradcam_heatmap,  # NEW: base64 PNG, raw heatmap only
                    "explanation_method": explanation_method,  # NEW: "grad-cam" | "score-cam" | None
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
