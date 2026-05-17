"""
Input Validation Utilities for Disease Prediction API
Provides validation functions for user inputs to ML prediction endpoints.
"""

import re
from typing import Tuple, List, Any, Optional


class ValidationError(ValueError):
    """Custom exception for validation errors"""
    pass


def validate_age(age: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate age input.
    
    Args:
        age: Age value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if age is None or age == "":
        return True, None  # Age is optional
    
    try:
        age_int = int(age)
    except (TypeError, ValueError):
        return False, "Age must be a valid number"
    
    if age_int < 0:
        return False, "Age cannot be negative"
    
    if age_int > 150:
        return False, "Age must be less than 150 years"
    
    return True, None


def validate_height(height_cm: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate height input in centimeters.
    
    Args:
        height_cm: Height value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if height_cm is None or height_cm == "":
        return True, None  # Height is optional
    
    try:
        height_float = float(height_cm)
    except (TypeError, ValueError):
        return False, "Height must be a valid number"
    
    if height_float < 30:
        return False, "Height must be at least 30 cm"
    
    if height_float > 300:
        return False, "Height must be less than 300 cm"
    
    return True, None


def validate_weight(weight_kg: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate weight input in kilograms.
    
    Args:
        weight_kg: Weight value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if weight_kg is None or weight_kg == "":
        return True, None  # Weight is optional
    
    try:
        weight_float = float(weight_kg)
    except (TypeError, ValueError):
        return False, "Weight must be a valid number"
    
    if weight_float < 1:
        return False, "Weight must be at least 1 kg"
    
    if weight_float > 700:
        return False, "Weight must be less than 700 kg"
    
    return True, None


def validate_disease_name(disease: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate disease name input.
    
    Args:
        disease: Disease name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not disease:
        return False, "Disease name is required"
    
    if not isinstance(disease, str):
        return False, "Disease name must be a string"
    
    disease_str = str(disease).strip()
    
    if len(disease_str) == 0:
        return False, "Disease name cannot be empty"
    
    if len(disease_str) > 100:
        return False, "Disease name is too long (maximum 100 characters)"
    
    # Only allow alphanumeric, spaces, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9\s_-]+$', disease_str):
        return False, "Disease name contains invalid characters"
    
    return True, None


def validate_symptoms_list(symptoms: Any, max_symptoms: int = 50) -> Tuple[bool, Optional[str]]:
    """
    Validate symptoms list input.
    
    Args:
        symptoms: Symptoms list to validate
        max_symptoms: Maximum number of symptoms allowed
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not symptoms:
        return False, "At least one symptom is required"
    
    if not isinstance(symptoms, list):
        return False, "Symptoms must be provided as a list"
    
    if len(symptoms) == 0:
        return False, "At least one symptom is required"
    
    if len(symptoms) > max_symptoms:
        return False, f"Too many symptoms provided (maximum {max_symptoms})"
    
    # Validate each symptom
    for idx, symptom in enumerate(symptoms):
        if not isinstance(symptom, str):
            return False, f"Symptom at index {idx} must be a string"
        
        symptom_str = str(symptom).strip()
        
        if len(symptom_str) == 0:
            return False, f"Symptom at index {idx} cannot be empty"
        
        if len(symptom_str) > 100:
            return False, f"Symptom at index {idx} is too long (maximum 100 characters)"
        
        # Check for suspicious patterns (basic XSS prevention)
        if re.search(r'[<>"\']', symptom_str):
            return False, f"Symptom at index {idx} contains invalid characters"
    
    return True, None


def validate_prediction_request(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate complete prediction request payload.
    
    Args:
        data: Request data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Request body must be a valid JSON object"
    
    # Validate disease (if provided)
    if 'disease' in data and data['disease']:
        is_valid, error = validate_disease_name(data['disease'])
        if not is_valid:
            return False, error
    
    # Validate symptoms (required)
    if 'symptoms' not in data:
        return False, "Symptoms field is required"
    
    is_valid, error = validate_symptoms_list(data['symptoms'])
    if not is_valid:
        return False, error
    
    # Validate optional fields
    if 'age' in data:
        is_valid, error = validate_age(data['age'])
        if not is_valid:
            return False, error
    
    if 'height_cm' in data:
        is_valid, error = validate_height(data['height_cm'])
        if not is_valid:
            return False, error
    
    if 'weight_kg' in data:
        is_valid, error = validate_weight(data['weight_kg'])
        if not is_valid:
            return False, error
    
    return True, None


def sanitize_string(text: str, max_length: int = 100) -> str:
    """
    Sanitize string input by removing potentially dangerous characters.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Remove dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(text))
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_image_file(file) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded image file.
    
    Args:
        file: Uploaded file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file:
        return False, "No image file provided"
    
    if not file.filename:
        return False, "Invalid file upload"
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        return False, f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size (limit to 10MB)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        return False, f"File too large. Maximum size: 10MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, None
