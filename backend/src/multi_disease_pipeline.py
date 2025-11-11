import joblib
import numpy as np
import os

# Central model paths
MODELS = {
    "heart": os.path.join("backend", "models", "heart_model.pkl"),
    "liver": os.path.join("backend", "models", "liver_model.pkl"),
    "diabetes": os.path.join("backend", "models", "diabetes_model.pkl")
}

def load_model(disease):
    """Load model for the selected disease."""
    if disease not in MODELS:
        raise ValueError(f"Unsupported disease: {disease}")
    return joblib.load(MODELS[disease])

def predict_disease(disease, features):
    """Predict disease outcome based on input features."""
    model = load_model(disease)
    features = np.array(features).reshape(1, -1)
    prediction = model.predict(features)[0]
    prob = model.predict_proba(features)[0].max() if hasattr(model, "predict_proba") else None
    return {"prediction": int(prediction), "confidence": round(float(prob), 4) if prob else None}
