"""
Input cleaning helpers for ML prediction requests.
This module provides functions to normalize and validate user-provided input data for disease prediction. It includes:
- Normalizing disease names and symptom labels into a consistent format.
- Validating that required fields are present and correctly formatted.
- Enforcing limits on the number of symptoms and acceptable ranges for numeric fields like age, height, and weight.
- Collecting metadata about any dropped symptoms for transparency and debugging purposes.

Also this was kept separate so that we can easily update things in future without any sudden huddles in the main codebase.
I have used "Type hints" format to make things more clear and easy to understand.
Proper regex pattern evaluation is used to make keep things more stable and efficient.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set

_SEPARATORS = re.compile(r"[\s\-]+")
_UNSAFE_KEY_CHARS = re.compile(r"[^a-z0-9_]+")
_MULTI_UNDERSCORE = re.compile(r"_+")


class PreprocessingError(ValueError):
    """
    Raised when a prediction payload cannot be cleaned safely.
    """


@dataclass
class CleanedPredictionInput:
    disease: Optional[str]
    symptoms: List[str]
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    heart_rate: Optional[float] = None
    blood_pressure_systolic: Optional[float] = None
    blood_pressure_diastolic: Optional[float] = None
    blood_glucose: Optional[float] = None
    temperature: Optional[float] = None
    dropped_symptoms: List[str] = field(default_factory=list)

    def metadata(self) -> Dict[str, Any]:
        return {
            "dropped_symptoms": self.dropped_symptoms,
            "normalized_symptoms_count": len(self.symptoms),
            "has_vitals": self.heart_rate is not None
            or self.blood_pressure_systolic is not None
            or self.blood_glucose is not None
            or self.temperature is not None,
        }


def normalize_key(value: Any) -> str:
    """
    Normalize user-facing labels into model-friendly snake_case keys.
    """
    if value is None:
        return ""

    normalized = str(value).strip().lower()
    normalized = _SEPARATORS.sub("_", normalized)
    normalized = _UNSAFE_KEY_CHARS.sub("", normalized)
    normalized = _MULTI_UNDERSCORE.sub("_", normalized)
    return normalized.strip("_")


def clean_disease(value: Any, required: bool = True) -> Optional[str]:
    disease = normalize_key(value)
    if required and not disease:
        raise PreprocessingError("Disease not specified")
    return disease or None


def clean_symptoms(
    symptoms: Any,
    valid_symptoms: Optional[Iterable[str]] = None,
    max_count: int = 50,
) -> tuple[List[str], List[str]]:
    if isinstance(symptoms, str):
        symptoms = [item.strip() for item in symptoms.split(",")]

    if not isinstance(symptoms, list):
        raise PreprocessingError("Symptoms must be provided as a list")

    if len(symptoms) > max_count:
        raise PreprocessingError(f"Too many symptoms provided (maximum {max_count})")

    valid_lookup: Optional[Set[str]] = None
    if valid_symptoms is not None:
        valid_lookup = {normalize_key(symptom) for symptom in valid_symptoms}

    cleaned: List[str] = []
    dropped: List[str] = []
    seen = set()

    for raw_symptom in symptoms:
        symptom = normalize_key(raw_symptom)
        if not symptom:
            continue

        if valid_lookup is not None and symptom not in valid_lookup:
            dropped.append(symptom)
            continue

        if symptom not in seen:
            cleaned.append(symptom)
            seen.add(symptom)

    if not cleaned:
        raise PreprocessingError("No valid symptoms provided")

    return cleaned, dropped


def clean_int(
    value: Any,
    field_name: str,
    min_value: int,
    max_value: int,
) -> Optional[int]:
    if value in (None, ""):
        return None

    try:
        cleaned = int(float(value))
    except (TypeError, ValueError):
        raise PreprocessingError(f"{field_name} must be a number")

    if cleaned < min_value or cleaned > max_value:
        raise PreprocessingError(
            f"{field_name} must be between {min_value} and {max_value}"
        )

    return cleaned


def clean_float(
    value: Any,
    field_name: str,
    min_value: float,
    max_value: float,
) -> Optional[float]:
    if value in (None, ""):
        return None

    try:
        cleaned = float(value)
    except (TypeError, ValueError):
        raise PreprocessingError(f"{field_name} must be a number")

    if not math.isfinite(cleaned):
        raise PreprocessingError(f"{field_name} must be a finite number")

    if cleaned < min_value or cleaned > max_value:
        raise PreprocessingError(
            f"{field_name} must be between {min_value:g} and {max_value:g}"
        )

    return cleaned


def clean_prediction_payload(
    payload: Dict[str, Any],
    valid_symptoms: Optional[Iterable[str]] = None,
    require_disease: bool = True,
) -> CleanedPredictionInput:
    if not isinstance(payload, dict):
        raise PreprocessingError("Request body must be valid JSON")

    symptoms, dropped = clean_symptoms(
        payload.get("symptoms", []),
        valid_symptoms=valid_symptoms,
    )

    return CleanedPredictionInput(
        disease=clean_disease(payload.get("disease"), required=require_disease),
        symptoms=symptoms,
        age=clean_int(payload.get("age"), "Age", 0, 120),
        height_cm=clean_float(payload.get("height_cm"), "Height", 30, 272),
        weight_kg=clean_float(payload.get("weight_kg"), "Weight", 1, 635),
        heart_rate=clean_float(payload.get("heart_rate"), "Heart Rate", 20, 250),
        blood_pressure_systolic=clean_float(
            payload.get("blood_pressure_systolic"), "Systolic Blood Pressure", 50, 250
        ),
        blood_pressure_diastolic=clean_float(
            payload.get("blood_pressure_diastolic"), "Diastolic Blood Pressure", 30, 150
        ),
        blood_glucose=clean_float(
            payload.get("blood_glucose"), "Blood Glucose", 20, 600
        ),
        temperature=clean_float(payload.get("temperature"), "Temperature", 25, 45),
        dropped_symptoms=dropped,
    )
