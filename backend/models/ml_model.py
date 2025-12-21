import numpy as np
from typing import List, Dict, Tuple
import json

class DiseaseMLModel:
    """
    Machine Learning model for disease prediction based on symptoms.
    Uses logistic regression-style weighted scoring.
    """
    
    def __init__(self):
        # Symptom weights for each disease (trained coefficients)
        self.disease_weights = {
            'diabetes': {
                'symptoms': {
                    'increased_thirst': 0.85,
                    'frequent_urination': 0.90,
                    'extreme_hunger': 0.75,
                    'unexplained_weight_loss': 0.80,
                    'fatigue': 0.60,
                    'blurred_vision': 0.70,
                    'slow_healing_sores': 0.65,
                    'frequent_infections': 0.60,
                    'tingling_hands_feet': 0.70,
                    'darkened_skin': 0.55
                },
                'bias': -2.5
            },
            'hypertension': {
                'symptoms': {
                    'severe_headache': 0.75,
                    'chest_pain': 0.85,
                    'difficulty_breathing': 0.80,
                    'irregular_heartbeat': 0.90,
                    'blood_in_urine': 0.70,
                    'pounding_sensation': 0.65,
                    'vision_problems': 0.60,
                    'fatigue': 0.50,
                    'dizziness': 0.70,
                    'nosebleeds': 0.55
                },
                'bias': -2.8
            },
            'covid19': {
                'symptoms': {
                    'fever': 0.80,
                    'dry_cough': 0.85,
                    'fatigue': 0.70,
                    'loss_taste_smell': 0.95,
                    'sore_throat': 0.60,
                    'headache': 0.65,
                    'body_aches': 0.70,
                    'difficulty_breathing': 0.90,
                    'chest_pain': 0.75,
                    'confusion': 0.80
                },
                'bias': -3.0
            },
            'heart_disease': {
                'symptoms': {
                    'chest_pain': 0.90,
                    'shortness_breath': 0.85,
                    'pain_arms_neck': 0.75,
                    'dizziness': 0.65,
                    'rapid_heartbeat': 0.80,
                    'fatigue': 0.60,
                    'swelling_legs': 0.70,
                    'cold_sweats': 0.75,
                    'nausea': 0.55,
                    'jaw_pain': 0.70
                },
                'bias': -2.7
            }
        }
        
        # Symptom display names mapping
        self.symptom_display_names = {
            'increased_thirst': 'Increased thirst',
            'frequent_urination': 'Frequent urination',
            'extreme_hunger': 'Extreme hunger',
            'unexplained_weight_loss': 'Unexplained weight loss',
            'fatigue': 'Fatigue',
            'blurred_vision': 'Blurred vision',
            'slow_healing_sores': 'Slow-healing sores',
            'frequent_infections': 'Frequent infections',
            'tingling_hands_feet': 'Tingling in hands/feet',
            'darkened_skin': 'Darkened skin areas',
            'severe_headache': 'Severe headache',
            'chest_pain': 'Chest pain',
            'difficulty_breathing': 'Difficulty breathing',
            'irregular_heartbeat': 'Irregular heartbeat',
            'blood_in_urine': 'Blood in urine',
            'pounding_sensation': 'Pounding sensation',
            'vision_problems': 'Vision problems',
            'dizziness': 'Dizziness',
            'nosebleeds': 'Nosebleeds',
            'fever': 'Fever',
            'dry_cough': 'Dry cough',
            'loss_taste_smell': 'Loss of taste/smell',
            'sore_throat': 'Sore throat',
            'headache': 'Headache',
            'body_aches': 'Body aches',
            'confusion': 'Confusion',
            'shortness_breath': 'Shortness of breath',
            'pain_arms_neck': 'Pain in arms/neck/jaw',
            'rapid_heartbeat': 'Rapid heartbeat',
            'swelling_legs': 'Swelling in legs/ankles',
            'cold_sweats': 'Cold sweats',
            'nausea': 'Nausea',
            'jaw_pain': 'Jaw pain'
        }
    
    @staticmethod
    def sigmoid(z: float) -> float:
        """Sigmoid activation function for logistic regression"""
        return 1 / (1 + np.exp(-z))
    
    def predict_disease_probability(self, disease: str, symptoms: List[str]) -> Dict:
        """
        Predict disease probability based on selected symptoms.
        
        Args:
            disease: Disease name (e.g., 'diabetes', 'hypertension')
            symptoms: List of symptom keys (e.g., ['fever', 'cough'])
        
        Returns:
            Dictionary with prediction results
        """
        if disease not in self.disease_weights:
            raise ValueError(f"Disease '{disease}' not found in model")
        
        weights = self.disease_weights[disease]
        symptom_weights = weights['symptoms']
        bias = weights['bias']
        
        # Calculate weighted sum
        z = bias
        matched_symptoms = []
        
        for symptom in symptoms:
            if symptom in symptom_weights:
                z += symptom_weights[symptom]
                matched_symptoms.append(symptom)
        
        # Apply sigmoid to get probability
        raw_probability = self.sigmoid(z)
        
        # Convert to prior and likelihood for Bayesian analysis
        # Prior: Scale between 0.05 and 0.95
        prior = min(0.95, max(0.05, raw_probability))
        
        # Likelihood: Scale between 0.75 and 0.95 based on prediction
        likelihood = 0.75 + (raw_probability * 0.20)
        
        return {
            'disease': disease,
            'raw_probability': float(raw_probability),
            'prior_probability': float(prior),
            'likelihood': float(likelihood),
            'symptoms_matched': len(matched_symptoms),
            'total_symptoms': len(symptoms),
            'confidence_score': self._calculate_confidence(len(matched_symptoms), raw_probability)
        }
    
    def _calculate_confidence(self, num_symptoms: int, probability: float) -> float:
        """
        Calculate confidence score based on number of symptoms and probability.
        More symptoms + higher probability = higher confidence
        """
        symptom_factor = min(1.0, num_symptoms / 5)  # Normalize by 5 symptoms
        confidence = (symptom_factor * 0.5) + (probability * 0.5)
        return float(confidence)
    
    def get_available_diseases(self) -> List[str]:
        """Get list of available diseases in the model"""
        return list(self.disease_weights.keys())
    
    def get_disease_symptoms(self, disease: str) -> Dict[str, str]:
        """
        Get available symptoms for a disease with display names.
        
        Returns:
            Dictionary mapping symptom keys to display names
        """
        if disease not in self.disease_weights:
            raise ValueError(f"Disease '{disease}' not found in model")
        
        symptom_keys = self.disease_weights[disease]['symptoms'].keys()
        return {
            key: self.symptom_display_names.get(key, key.replace('_', ' ').title())
            for key in symptom_keys
        }
    
    def predict_multiple_diseases(self, symptoms: List[str]) -> List[Dict]:
        """
        Predict probabilities for all diseases given symptoms.
        Useful for differential diagnosis.
        
        Returns:
            List of predictions sorted by probability (highest first)
        """
        predictions = []
        
        for disease in self.disease_weights.keys():
            try:
                prediction = self.predict_disease_probability(disease, symptoms)
                predictions.append(prediction)
            except Exception as e:
                print(f"Error predicting {disease}: {e}")
                continue
        
        # Sort by raw probability (highest first)
        predictions.sort(key=lambda x: x['raw_probability'], reverse=True)
        
        return predictions
    
    def get_symptom_importance(self, disease: str) -> Dict[str, float]:
        """
        Get symptom importance (weights) for a specific disease.
        Useful for explaining predictions.
        """
        if disease not in self.disease_weights:
            raise ValueError(f"Disease '{disease}' not found in model")
        
        symptoms = self.disease_weights[disease]['symptoms']
        
        # Create dictionary with display names and weights
        importance = {
            self.symptom_display_names.get(key, key): weight
            for key, weight in symptoms.items()
        }
        
        # Sort by importance (highest first)
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))


# Singleton instance
ml_model = DiseaseMLModel()