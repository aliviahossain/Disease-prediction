"""
Comprehensive tests for input validation utilities
"""
import pytest
from backend.utils.validation import (
    validate_age,
    validate_height,
    validate_weight,
    validate_disease_name,
    validate_symptoms_list,
    validate_prediction_request,
    validate_image_file,
    sanitize_string,
    ValidationError
)
from io import BytesIO


# ============================================================================
# Age Validation Tests
# ============================================================================

def test_validate_age_valid():
    """Test valid age inputs"""
    assert validate_age(25) == (True, None)
    assert validate_age(0) == (True, None)
    assert validate_age(120) == (True, None)
    assert validate_age("45") == (True, None)


def test_validate_age_optional():
    """Test that age is optional"""
    assert validate_age(None) == (True, None)
    assert validate_age("") == (True, None)


def test_validate_age_negative():
    """Test that negative age is rejected"""
    is_valid, error = validate_age(-5)
    assert not is_valid
    assert "negative" in error.lower()


def test_validate_age_too_high():
    """Test that unrealistic age is rejected"""
    is_valid, error = validate_age(200)
    assert not is_valid
    assert "150" in error


def test_validate_age_non_numeric():
    """Test that non-numeric age is rejected"""
    is_valid, error = validate_age("abc")
    assert not is_valid
    assert "number" in error.lower()


# ============================================================================
# Height Validation Tests
# ============================================================================

def test_validate_height_valid():
    """Test valid height inputs"""
    assert validate_height(170) == (True, None)
    assert validate_height(150.5) == (True, None)
    assert validate_height("180") == (True, None)


def test_validate_height_optional():
    """Test that height is optional"""
    assert validate_height(None) == (True, None)
    assert validate_height("") == (True, None)


def test_validate_height_too_low():
    """Test that unrealistic low height is rejected"""
    is_valid, error = validate_height(20)
    assert not is_valid
    assert "30" in error


def test_validate_height_too_high():
    """Test that unrealistic high height is rejected"""
    is_valid, error = validate_height(350)
    assert not is_valid
    assert "300" in error


def test_validate_height_non_numeric():
    """Test that non-numeric height is rejected"""
    is_valid, error = validate_height("tall")
    assert not is_valid
    assert "number" in error.lower()


# ============================================================================
# Weight Validation Tests
# ============================================================================

def test_validate_weight_valid():
    """Test valid weight inputs"""
    assert validate_weight(70) == (True, None)
    assert validate_weight(55.5) == (True, None)
    assert validate_weight("80") == (True, None)


def test_validate_weight_optional():
    """Test that weight is optional"""
    assert validate_weight(None) == (True, None)
    assert validate_weight("") == (True, None)


def test_validate_weight_too_low():
    """Test that unrealistic low weight is rejected"""
    is_valid, error = validate_weight(0.5)
    assert not is_valid
    assert "1" in error


def test_validate_weight_too_high():
    """Test that unrealistic high weight is rejected"""
    is_valid, error = validate_weight(800)
    assert not is_valid
    assert "700" in error


# ============================================================================
# Disease Name Validation Tests
# ============================================================================

def test_validate_disease_name_valid():
    """Test valid disease names"""
    assert validate_disease_name("diabetes") == (True, None)
    assert validate_disease_name("diabetes_type_2") == (True, None)
    assert validate_disease_name("COVID-19") == (True, None)


def test_validate_disease_name_empty():
    """Test that empty disease name is rejected"""
    is_valid, error = validate_disease_name("")
    assert not is_valid
    assert "required" in error.lower() or "empty" in error.lower()


def test_validate_disease_name_none():
    """Test that None disease name is rejected"""
    is_valid, error = validate_disease_name(None)
    assert not is_valid


def test_validate_disease_name_too_long():
    """Test that overly long disease name is rejected"""
    long_name = "a" * 150
    is_valid, error = validate_disease_name(long_name)
    assert not is_valid
    assert "long" in error.lower()


def test_validate_disease_name_invalid_characters():
    """Test that disease names with invalid characters are rejected"""
    is_valid, error = validate_disease_name("diabetes<script>")
    assert not is_valid
    assert "invalid" in error.lower()


# ============================================================================
# Symptoms List Validation Tests
# ============================================================================

def test_validate_symptoms_list_valid():
    """Test valid symptoms lists"""
    assert validate_symptoms_list(["fever", "cough"]) == (True, None)
    assert validate_symptoms_list(["headache"]) == (True, None)


def test_validate_symptoms_list_empty():
    """Test that empty symptoms list is rejected"""
    is_valid, error = validate_symptoms_list([])
    assert not is_valid
    assert "required" in error.lower()


def test_validate_symptoms_list_none():
    """Test that None symptoms is rejected"""
    is_valid, error = validate_symptoms_list(None)
    assert not is_valid


def test_validate_symptoms_list_not_list():
    """Test that non-list symptoms is rejected"""
    is_valid, error = validate_symptoms_list("fever, cough")
    assert not is_valid
    assert "list" in error.lower()


def test_validate_symptoms_list_too_many():
    """Test that too many symptoms are rejected"""
    symptoms = [f"symptom_{i}" for i in range(60)]
    is_valid, error = validate_symptoms_list(symptoms, max_symptoms=50)
    assert not is_valid
    assert "50" in error


def test_validate_symptoms_list_non_string_item():
    """Test that non-string symptom items are rejected"""
    is_valid, error = validate_symptoms_list(["fever", 123, "cough"])
    assert not is_valid
    assert "string" in error.lower()


def test_validate_symptoms_list_empty_string():
    """Test that empty string symptoms are rejected"""
    is_valid, error = validate_symptoms_list(["fever", "", "cough"])
    assert not is_valid
    assert "empty" in error.lower()


def test_validate_symptoms_list_too_long_item():
    """Test that overly long symptom items are rejected"""
    long_symptom = "a" * 150
    is_valid, error = validate_symptoms_list(["fever", long_symptom])
    assert not is_valid
    assert "long" in error.lower()


def test_validate_symptoms_list_invalid_characters():
    """Test that symptoms with invalid characters are rejected"""
    is_valid, error = validate_symptoms_list(["fever", "cough<script>"])
    assert not is_valid
    assert "invalid" in error.lower()


# ============================================================================
# Complete Request Validation Tests
# ============================================================================

def test_validate_prediction_request_valid_minimal():
    """Test valid minimal prediction request"""
    data = {
        "disease": "diabetes",
        "symptoms": ["fever", "fatigue"]
    }
    assert validate_prediction_request(data) == (True, None)


def test_validate_prediction_request_valid_complete():
    """Test valid complete prediction request"""
    data = {
        "disease": "diabetes",
        "symptoms": ["fever", "fatigue"],
        "age": 45,
        "height_cm": 170,
        "weight_kg": 75
    }
    assert validate_prediction_request(data) == (True, None)


def test_validate_prediction_request_missing_symptoms():
    """Test that request without symptoms is rejected"""
    data = {"disease": "diabetes"}
    is_valid, error = validate_prediction_request(data)
    assert not is_valid
    assert "symptoms" in error.lower()


def test_validate_prediction_request_invalid_age():
    """Test that request with invalid age is rejected"""
    data = {
        "disease": "diabetes",
        "symptoms": ["fever"],
        "age": -5
    }
    is_valid, error = validate_prediction_request(data)
    assert not is_valid


def test_validate_prediction_request_invalid_height():
    """Test that request with invalid height is rejected"""
    data = {
        "disease": "diabetes",
        "symptoms": ["fever"],
        "height_cm": 10
    }
    is_valid, error = validate_prediction_request(data)
    assert not is_valid


def test_validate_prediction_request_not_dict():
    """Test that non-dict request is rejected"""
    is_valid, error = validate_prediction_request("not a dict")
    assert not is_valid
    assert "JSON" in error or "object" in error.lower()


# ============================================================================
# String Sanitization Tests
# ============================================================================

def test_sanitize_string_removes_dangerous_chars():
    """Test that dangerous characters are removed"""
    result = sanitize_string("hello<script>world")
    assert "<" not in result
    assert ">" not in result
    assert "script" in result


def test_sanitize_string_limits_length():
    """Test that string length is limited"""
    long_string = "a" * 200
    result = sanitize_string(long_string, max_length=50)
    assert len(result) == 50


def test_sanitize_string_empty():
    """Test sanitization of empty string"""
    assert sanitize_string("") == ""
    assert sanitize_string(None) == ""


# ============================================================================
# Image File Validation Tests
# ============================================================================

def test_validate_image_file_valid():
    """Test valid image file"""
    file = BytesIO(b"fake image data")
    file.filename = "test.jpg"
    assert validate_image_file(file) == (True, None)


def test_validate_image_file_none():
    """Test that None file is rejected"""
    is_valid, error = validate_image_file(None)
    assert not is_valid


def test_validate_image_file_invalid_extension():
    """Test that invalid file extension is rejected"""
    file = BytesIO(b"fake data")
    file.filename = "test.exe"
    is_valid, error = validate_image_file(file)
    assert not is_valid
    assert "type" in error.lower()


def test_validate_image_file_empty():
    """Test that empty file is rejected"""
    file = BytesIO(b"")
    file.filename = "test.jpg"
    is_valid, error = validate_image_file(file)
    assert not is_valid
    assert "empty" in error.lower()


# ============================================================================
# Security Tests
# ============================================================================

def test_validation_prevents_xss():
    """Test that validation prevents XSS attacks"""
    malicious_data = {
        "disease": "diabetes<script>alert('xss')</script>",
        "symptoms": ["fever<script>", "cough"]
    }
    is_valid, error = validate_prediction_request(malicious_data)
    assert not is_valid


def test_validation_prevents_sql_injection():
    """Test that validation prevents SQL injection patterns"""
    malicious_data = {
        "disease": "diabetes'; DROP TABLE users; --",
        "symptoms": ["fever"]
    }
    is_valid, error = validate_prediction_request(malicious_data)
    assert not is_valid
