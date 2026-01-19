import io
import numpy as np
import os
from PIL import Image
from flask import Flask, Blueprint, render_template, request, jsonify
from functools import lru_cache

# Supress TensorFlow Logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# Supress np.object warnings
import warnings
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=".*np.object.*"
)

# ✅ LAZY LOAD: Import TensorFlow only when actually needed (not at module load)
@lru_cache(maxsize=1)
def _load_tensorflow():
    """Lazy load TensorFlow to avoid blocking app startup"""
    from tensorflow.keras.models import load_model
    from tensorflow.keras.applications.resnet50 import preprocess_input
    return load_model, preprocess_input

def load_model(*args, **kwargs):
    """Wrapper that lazy-loads TensorFlow"""
    _load_model, _ = _load_tensorflow()
    return _load_model(*args, **kwargs)

def preprocess_input(*args, **kwargs):
    """Wrapper that lazy-loads TensorFlow"""
    _, _preprocess_input = _load_tensorflow()
    return _preprocess_input(*args, **kwargs)

predict_disease_type_bp = Blueprint("disease-type", __name__)

# ---------------- CONFIG ----------------
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BACKEND_DIR,
    "models",
    "resnet50_models",
    "eye_disease_resnet50_fp16.keras"
)

# print("MODEL PATH:", MODEL_PATH)
# print("MODEL EXISTS:", os.path.exists(MODEL_PATH))

CLASS_NAMES = [
    "Cataract",
    "Diabetic Retinopathy",
    "Glaucoma",
    "Normal",
]

IMG_SIZE = (224, 224)
# ----------------------------------------

# Load model ONCE at startup
model = load_model(MODEL_PATH, compile=False)

# Preprocess image for prediction
def preprocess_image(file):
    img = Image.open(file).convert("RGB")
    img = img.resize(IMG_SIZE)

    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    return img_array

# Route to handle disease type prediction
@predict_disease_type_bp.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files["image"]
    disease_type = request.form.get("type", "eye")

    img = preprocess_image(image_file)
    preds = model.predict(img)[0]

    idx = int(np.argmax(preds))
    confidence = float(preds[idx])

    return jsonify({
        "prediction": CLASS_NAMES[idx],
        "confidence": round(confidence * 100, 2),
        "type": disease_type
    }), 200