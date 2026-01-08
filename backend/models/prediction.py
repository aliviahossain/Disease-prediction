"""
PredictionHistory Model
Stores all disease predictions for dashboard analytics.
"""

from backend import db
from datetime import datetime
import json


class PredictionHistory(db.Model):
    """
    Model to store disease prediction records.
    Used for doctor dashboard analytics and patient history.
    """
    __tablename__ = 'prediction_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Patient info (nullable for anonymous predictions)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    patient_age = db.Column(db.Integer, nullable=True)
    
    # Prediction details
    disease = db.Column(db.String(100), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)  # JSON string of symptoms list
    
    # Probability scores
    ml_probability = db.Column(db.Float, nullable=False)
    bayesian_posterior = db.Column(db.Float, nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    
    # Risk assessment
    risk_level = db.Column(db.String(20), nullable=False, index=True)  # low, medium, high, critical
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('predictions', lazy=True))
    
    def __repr__(self):
        return f"PredictionHistory('{self.disease}', risk='{self.risk_level}', created='{self.created_at}')"
    
    def get_symptoms_list(self):
        """Parse symptoms JSON string to list"""
        try:
            return json.loads(self.symptoms)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_symptoms_list(self, symptoms_list):
        """Convert symptoms list to JSON string"""
        self.symptoms = json.dumps(symptoms_list)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'disease': self.disease,
            'symptoms': self.get_symptoms_list(),
            'ml_probability': self.ml_probability,
            'bayesian_posterior': self.bayesian_posterior,
            'risk_level': self.risk_level,
            'patient_age': self.patient_age,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
