# backend/models/prediction.py

import os
import numpy as np
from tensorflow.keras.preprocessing import image

# Configurable confidence threshold
CONFIDENCE_THRESHOLD = float(
    os.getenv("PREDICTION_CONFIDENCE_THRESHOLD", 0.65)
)

# Example disease classes
CLASS_NAMES = [
    "Cataract",
    "Diabetic Retinopathy",
    "Glaucoma",
    "Normal"
]


def predict_disease(model, img_path, target_size=(224, 224)):
    """
    Predict disease with uncertainty handling.
    Returns:
        {
            "status": "success" | "uncertain",
            "disease": str | None,
            "confidence": float,
            "message": str
        }
    """

    try:
        # Load image
        img = image.load_img(img_path, target_size=target_size)
        img_array = image.img_to_array(img)

        # Normalize
        img_array = img_array / 255.0

        # Expand dimensions
        img_array = np.expand_dims(img_array, axis=0)

        # Predict probabilities
        predictions = model.predict(img_array)

        # Get highest confidence
        confidence = float(np.max(predictions))

        # Get predicted class index
        predicted_index = int(np.argmax(predictions))

        # Uncertainty Handling
        if confidence < CONFIDENCE_THRESHOLD:
            return {
                "status": "uncertain",
                "disease": None,
                "confidence": round(confidence, 4),
                "message": (
                    "Insufficient data to predict reliably. "
                    "Please provide a clearer image or more information."
                )
            }

        predicted_disease = CLASS_NAMES[predicted_index]

        return {
            "status": "success",
            "disease": predicted_disease,
            "confidence": round(confidence, 4),
            "message": "Prediction generated successfully."
        }

    except Exception as e:
        return {
            "status": "error",
            "disease": None,
            "confidence": 0.0,
            "message": f"Prediction failed: {str(e)}"
        }