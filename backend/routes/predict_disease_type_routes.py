# Suppress numpy warnings
import warnings
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=".*np.object.*"
)
warnings.filterwarnings(
    "ignore",
    message=".*tf.lite.Interpreter is deprecated.*",
    category=UserWarning
)
warnings.filterwarnings(
    "ignore",
    message=".*np.object.*",
    category=FutureWarning
)

import numpy as np
import os
from PIL import Image
from flask import Blueprint, request, jsonify
import tensorflow as tf

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
            BACKEND_DIR,
            "models",
            "resnet50_models",
            "eye_disease_resnet50_fp16.keras"
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
            BACKEND_DIR,
            "models",
            "resnet50_models",
            "skin_model.tflite"
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
    }
}

# Model caches
KERAS_MODEL_CACHE = {}
TFLITE_MODEL_CACHE = {}

# loads keras model in the KERAS_MODEL_CACHE (for eye disease prediction)
def load_keras_model(model_type):
    if model_type not in KERAS_MODEL_CACHE:
        path = MODEL_CONFIG[model_type]["path"]
        print(f"Loading Keras model: {model_type}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found: {path}")

        KERAS_MODEL_CACHE[model_type] = tf.keras.models.load_model(
            path, compile=False
        )
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


#  Main prediction route
@predict_disease_type_bp.route("/predict", methods=["POST"])
def predict():
    # Accept file as "image" or "file"
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    image_file = request.files["image"]

    # Accept type from form or JSON
    model_type = (
        request.form.get("type")
        or (request.json.get("type") if request.is_json else None)
        or "eyes"
    ).lower()

    print("model_type: ", model_type)

    if model_type not in MODEL_CONFIG:
        return jsonify({
            "error": f"Invalid type '{model_type}'. Use one of: {list(MODEL_CONFIG.keys())}"
        }), 400

    print(model_type not in MODEL_CONFIG)
    
    try:
        # 1. Preprocess image
        img_array = preprocess_image(image_file, model_type)

        # 2. Run inference model to get predictions
        if MODEL_CONFIG[model_type]["format"] == "keras":
            preds = run_keras_inference(model_type, img_array)
        else:
            preds = run_tflite_inference(model_type, img_array)
        
        # 3. Get predicted class and confidence
        idx = int(np.argmax(preds))
        confidence = float(preds[idx])

        return jsonify({
            "prediction": MODEL_CONFIG[model_type]["class_names"][idx],
            "confidence": round(confidence * 100, 2),
            "type": model_type
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500