"""Minimal synthetic patient generator for testing rare disease combinations."""

import logging
import random
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from backend.models.ml_model import DiseaseMLModel

logger = logging.getLogger(__name__)


class SyntheticPatientGenerator:
    """Generate synthetic patient profiles for model testing."""

    def __init__(self):
        self.ml_model = DiseaseMLModel()

    def generate_patient(
        self,
        disease: Optional[str] = None,
        symptom_intensity: float = 0.5,
        age: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate single synthetic patient.
        
        Args:
            disease: Disease name (random if None)
            symptom_intensity: 0.0-1.0 scaling for symptom probability
            age: Patient age (random if None)
        """
        if disease is None:
            disease = random.choice(list(self.ml_model.disease_weights.keys()))

        if age is None:
            age = random.randint(20, 80)

        disease_lower = disease.lower()
        
        # Get symptoms for disease
        if disease_lower not in self.ml_model.disease_weights:
            symptoms = []
        else:
            disease_config = self.ml_model.disease_weights[disease_lower]
            symptom_weights = disease_config.get("symptoms", {})
            symptoms = [
                symptom
                for symptom, weight in symptom_weights.items()
                if random.random() < weight * symptom_intensity
            ]

        # Generate vitals
        vitals = self._generate_vitals(disease_lower, age)
        
        return {
            "disease": disease_lower,
            "symptoms": symptoms,
            "age": age,
            "vitals": vitals,
            "is_synthetic": True,
        }

    def _generate_vitals(self, disease: str, age: int) -> Dict[str, float]:
        """Generate realistic vitals based on disease and age."""
        vitals = {
            "heart_rate": round(np.random.normal(72, 10), 1),
            "blood_pressure_systolic": round(np.random.normal(120, 10), 1),
            "blood_pressure_diastolic": round(np.random.normal(80, 8), 1),
            "blood_glucose": round(np.random.normal(100, 15), 1),
            "temperature": round(np.random.normal(37.0, 0.3), 1),
        }

        # Disease-specific adjustments
        if disease == "hypertension":
            vitals["blood_pressure_systolic"] = round(np.random.normal(150, 20), 1)
            vitals["blood_pressure_diastolic"] = round(np.random.normal(95, 10), 1)
        elif disease == "diabetes":
            vitals["blood_glucose"] = round(np.random.normal(180, 40), 1)
        elif disease in ["influenza", "covid19", "malaria"]:
            vitals["temperature"] = round(np.random.normal(38.5, 1.0), 1)

        # Age adjustment
        if age > 65:
            vitals["blood_pressure_systolic"] += 5

        return vitals

    def generate_population(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate population of synthetic patients."""
        return [self.generate_patient() for _ in range(count)]

    def generate_rare_combinations(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate rare symptom combinations across diseases."""
        rare = []
        diseases = list(self.ml_model.disease_weights.keys())
        
        for _ in range(count):
            primary = random.choice(diseases)
            secondary = random.choice([d for d in diseases if d != primary])
            
            patient = self.generate_patient(disease=primary, symptom_intensity=0.3)
            
            # Add rare symptoms from secondary disease
            if secondary in self.ml_model.disease_weights:
                secondary_symptoms = list(
                    self.ml_model.disease_weights[secondary].get("symptoms", {}).keys()
                )
                if secondary_symptoms:
                    patient["symptoms"].append(random.choice(secondary_symptoms))
            
            patient["rarity_note"] = f"Mixing {primary} with {secondary} symptoms"
            rare.append(patient)
        
        return rare

    def generate_edge_cases(self) -> List[Dict[str, Any]]:
        """Generate edge cases for stress testing."""
        return [
            self.generate_patient(symptom_intensity=0.95),  # High confidence
            self.generate_patient(symptom_intensity=0.1),   # Low confidence
            self.generate_patient(age=5),                    # Pediatric
            self.generate_patient(age=90),                   # Geriatric
        ]

    def calculate_ml_score(self, disease: str, symptoms: List[str]) -> float:
        """
        Calculate ML probability score for synthetic patient.
        
        Args:
            disease: Disease name
            symptoms: List of symptom names
            
        Returns:
            Probability score 0.0-1.0
        """
        disease_lower = disease.lower()
        
        if disease_lower not in self.ml_model.disease_weights:
            return 0.5
        
        config = self.ml_model.disease_weights[disease_lower]
        weights = config.get("symptoms", {})
        bias = config.get("bias", -2.5)
        
        score = bias
        for symptom in symptoms:
            if symptom in weights:
                score += weights[symptom]
        
        # Sigmoid normalization
        prob = 1.0 / (1.0 + 2.71828 ** (-score))
        return round(max(0.0, min(1.0, prob)), 4)
