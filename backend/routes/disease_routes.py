from flask import Blueprint, request, jsonify, render_template
import csv
import os
import logging
from typing import Dict, Optional, Tuple

from backend.utils.calculator import bayesian_survival

# Configure logging
logger = logging.getLogger(__name__)

disease_bp = Blueprint("disease", __name__)

# Constants
CSV_FILENAME = "hospital_data.csv"
VALID_TEST_RESULTS = {"positive", "negative"}


def get_csv_path() -> str:
    """
    Get the absolute path to the hospital data CSV file.
    
    Returns:
        str: Absolute path to the CSV file
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, CSV_FILENAME)


def load_diseases_from_csv() -> Tuple[list, Optional[str]]:
    """
    Load disease names from the CSV file.
    
    Returns:
        Tuple[list, Optional[str]]: List of disease names and error message if any
    """
    csv_path = get_csv_path()
    diseases = []
    error = None
    
    try:
        if not os.path.exists(csv_path):
            error = f"Data file not found at {csv_path}"
            logger.error(error)
            return diseases, error
            
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            
            if "Disease" not in reader.fieldnames:
                error = "CSV file missing 'Disease' column"
                logger.error(error)
                return diseases, error
                
            diseases = [row["Disease"] for row in reader if row.get("Disease")]
            logger.info(f"Successfully loaded {len(diseases)} diseases from CSV")
            
    except PermissionError:
        error = f"Permission denied reading {csv_path}"
        logger.error(error)
    except csv.Error as e:
        error = f"CSV parsing error: {str(e)}"
        logger.error(error)
    except Exception as e:
        error = f"Unexpected error loading diseases: {str(e)}"
        logger.exception(error)
    
    return diseases, error


def find_disease_data(disease_name: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Find disease data from CSV by disease name.
    
    Args:
        disease_name: Name of the disease to search for
        
    Returns:
        Tuple[Optional[Dict], Optional[str]]: Disease data dict and error message if any
    """
    if not disease_name or not isinstance(disease_name, str):
        return None, "Disease name must be a non-empty string"
    
    csv_path = get_csv_path()
    
    try:
        if not os.path.exists(csv_path):
            return None, f"Data file not found at {csv_path}"
            
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            
            required_fields = {"Disease", "Prevalence", "Sensitivity", "FalsePositive"}
            if not required_fields.issubset(set(reader.fieldnames or [])):
                missing = required_fields - set(reader.fieldnames or [])
                return None, f"CSV missing required columns: {missing}"
            
            for row in reader:
                if row["Disease"].lower() == disease_name.lower():
                    try:
                        return {
                            "prevalence": float(row["Prevalence"]),
                            "sensitivity": float(row["Sensitivity"]),
                            "false_positive": float(row["FalsePositive"])
                        }, None
                    except (ValueError, KeyError) as e:
                        return None, f"Invalid data format for disease '{disease_name}': {str(e)}"
            
            return None, f"Disease '{disease_name}' not found in database"
            
    except Exception as e:
        error = f"Error reading disease data: {str(e)}"
        logger.exception(error)
        return None, error


def validate_probability(name: str, value: float) -> Optional[str]:
    """
    Validate that a probability value is between 0 and 1.
    
    Args:
        name: Name of the parameter for error messages
        value: Value to validate
        
    Returns:
        Optional[str]: Error message if invalid, None if valid
    """
    if not isinstance(value, (int, float)):
        return f"{name} must be a number"
    if not (0.0 <= value <= 1.0):
        return f"{name} must be between 0 and 1 (inclusive). Got {value}"
    return None


@disease_bp.route("/")
def home():
    """
    Render the main page with list of available diseases.
    """
    diseases, error = load_diseases_from_csv()
    
    if error:
        logger.warning(f"Loading diseases with error: {error}")
    
    return render_template("main.html", diseases=diseases)


@disease_bp.route("/preset", methods=["POST"])
def preset():
    """
    Calculate disease probability for a preset disease from the database.
    
    Expected JSON payload:
        {
            "disease": "disease_name"
        }
    
    Returns:
        JSON with posterior probability and prior, or error message
    """
    try:
        if not request.json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        disease_name = request.json.get("disease")
        
        if not disease_name:
            return jsonify({"error": "Missing 'disease' parameter"}), 400
        
        disease_data, error = find_disease_data(disease_name)
        
        if error:
            logger.warning(f"Disease lookup failed: {error}")
            return jsonify({"error": error}), 404 if "not found" in error else 500
        
        # Calculate posterior probability
        p_d_given_pos = bayesian_survival(
            disease_data["prevalence"],
            disease_data["sensitivity"],
            disease_data["false_positive"]
        )
        
        logger.info(f"Calculated preset for disease '{disease_name}': {p_d_given_pos:.4f}")
        
        return jsonify({
            "p_d_given_pos": round(p_d_given_pos, 4),
            "prior": disease_data["prevalence"]
        })
        
    except Exception as e:
        error_msg = f"Unexpected error in preset calculation: {str(e)}"
        logger.exception(error_msg)
        return jsonify({"error": "Internal server error"}), 500


@disease_bp.route("/disease", methods=["POST"])
def disease():
    """
    Calculate disease probability with custom input parameters.
    
    Expected JSON payload:
        {
            "pD": float (0-1),
            "sensitivity": float (0-1),
            "falsePositive": float (0-1),
            "testResult": "positive" or "negative" (optional, defaults to "positive")
        }
    
    Returns:
        JSON with posterior probability and test result, or error message
    """
    try:
        if not request.json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.json
        
        # Extract and validate inputs
        try:
            p_d = float(data.get("pD", 0))
            sensitivity = float(data.get("sensitivity", 0))
            false_pos = float(data.get("falsePositive", 0))
        except (TypeError, ValueError) as e:
            return jsonify({"error": f"Invalid numeric input: {str(e)}"}), 400
        
        test_result = data.get("testResult", "positive").lower()
        
        # Validate probability ranges
        for name, value in [
            ("Prevalence", p_d),
            ("Sensitivity", sensitivity),
            ("FalsePositive", false_pos)
        ]:
            error = validate_probability(name, value)
            if error:
                return jsonify({"error": error}), 400
        
        # Validate test result
        if test_result not in VALID_TEST_RESULTS:
            return jsonify({
                "error": f"testResult must be one of {VALID_TEST_RESULTS}. Got '{test_result}'"
            }), 400
        
        specificity = 1 - false_pos
        
        # Calculate posterior probability based on test result
        if test_result == "positive":
            numerator = sensitivity * p_d
            denominator = numerator + (1 - specificity) * (1 - p_d)
        else:  # negative
            numerator = (1 - sensitivity) * p_d
            denominator = numerator + specificity * (1 - p_d)
        
        # Handle division by zero
        if denominator == 0:
            logger.warning(f"Division by zero with inputs: pD={p_d}, sens={sensitivity}, fp={false_pos}")
            return jsonify({
                "error": "Calculation error: Division by zero. Please check your input values."
            }), 400
        
        p_d_given_result = numerator / denominator
        
        logger.info(
            f"Custom calculation: pD={p_d}, sens={sensitivity}, fp={false_pos}, "
            f"result={test_result}, posterior={p_d_given_result:.4f}"
        )
        
        return jsonify({
            "p_d_given_result": round(p_d_given_result, 4),
            "test_result": test_result
        })
        
    except Exception as e:
        error_msg = f"Unexpected error in disease calculation: {str(e)}"
        logger.exception(error_msg)
        return jsonify({"error": "Internal server error"}), 500
