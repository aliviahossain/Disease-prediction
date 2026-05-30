# backend/models/prediction.py
import os
import json
import numpy as np
from keras.utils import load_img, img_to_array
from backend import db
from sqlalchemy import CheckConstraint
from datetime import datetime
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
    try:
        # Load image
        img = load_img(img_path, target_size=target_size)
        img_array = img_to_array(img)

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

class PredictionHistory(db.Model):
# Example disease classes
    CLASS_NAMES = [
        "Cataract",
        "Diabetic Retinopathy",
        "Glaucoma",
        "Normal"
]

    __tablename__ = 'prediction_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Patient info (nullable for anonymous predictions)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    patient_age = db.Column(db.Integer, nullable=True)
    __table_args__ = (
    CheckConstraint('patient_age >= 0', name='check_patient_age_non_negative'),
    )
    # Prediction details
    disease = db.Column(db.String(100), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)  # JSON string of symptoms list
    
    # Probability scores
    ml_probability = db.Column(db.Float, nullable=False)
    bayesian_posterior = db.Column(db.Float, nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    survival_probability = db.Column(db.Float, nullable=True) # Dynamically calculated temporal survival probability
    
    # Patient Vitals (nullable, optional)
    heart_rate = db.Column(db.Float, nullable=True)
    blood_pressure_systolic = db.Column(db.Float, nullable=True)
    blood_pressure_diastolic = db.Column(db.Float, nullable=True)
    blood_glucose = db.Column(db.Float, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    
    # Risk assessment
    risk_level = db.Column(db.String(20), nullable=False, index=True)  # low, medium, high, critical
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('predictions', lazy=True))
    
    def __repr__(self):
        return f"PredictionHistory('{self.disease}', risk='{self.risk_level}', created='{self.created_at}')"
    
    def get_symptoms_list(self):
        try:
            return json.loads(self.symptoms)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_symptoms_list(self, symptoms_list):
        self.symptoms = json.dumps(symptoms_list)
    
    def to_dict(self):
        return {
            'id': self.id,
            'disease': self.disease,
            'symptoms': self.get_symptoms_list(),
            'ml_probability': self.ml_probability,
            'bayesian_posterior': self.bayesian_posterior,
            'survival_probability': self.survival_probability,
            'heart_rate': self.heart_rate,
            'blood_pressure_systolic': self.blood_pressure_systolic,
            'blood_pressure_diastolic': self.blood_pressure_diastolic,
            'blood_glucose': self.blood_glucose,
            'temperature': self.temperature,
            'risk_level': self.risk_level,
            'patient_age': self.patient_age,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

