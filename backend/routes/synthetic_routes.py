"""Minimal synthetic patient API endpoints."""

import logging
from flask import Blueprint, request, jsonify
from backend.services.synthetic_patient_service import SyntheticPatientGenerator
from backend.middleware.error_handler import handle_errors

logger = logging.getLogger(__name__)

synthetic_bp = Blueprint("synthetic", __name__, url_prefix="/api/synthetic")


@synthetic_bp.route("/generate", methods=["POST"])
@handle_errors
def generate_patient():
    """Generate single synthetic patient for testing."""
    data = request.get_json() or {}
    
    try:
        generator = SyntheticPatientGenerator()
        patient = generator.generate_patient(
            disease=data.get("disease"),
            symptom_intensity=float(data.get("symptom_intensity", 0.5)),
            age=data.get("age"),
        )
        
        # Calculate prediction score
        ml_score = generator.calculate_ml_score(patient["disease"], patient["symptoms"])
        patient["ml_score"] = ml_score
        
        return jsonify({"status": "success", "patient": patient}), 200
    except Exception as e:
        logger.error(f"Error generating patient: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400


@synthetic_bp.route("/population", methods=["POST"])
@handle_errors
def generate_population():
    """Generate population of synthetic patients."""
    data = request.get_json() or {}
    
    try:
        count = int(data.get("count", 50))
        count = max(1, min(500, count))
        
        generator = SyntheticPatientGenerator()
        population = generator.generate_population(count)
        
        # Add ML scores for each patient
        for patient in population:
            patient["ml_score"] = generator.calculate_ml_score(patient["disease"], patient["symptoms"])
        
        return jsonify({"status": "success", "count": len(population), "population": population}), 200
    except Exception as e:
        logger.error(f"Error generating population: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400


@synthetic_bp.route("/rare", methods=["GET"])
@handle_errors
def rare_combinations():
    """Generate rare symptom combinations."""
    try:
        count = int(request.args.get("count", 10))
        count = max(1, min(100, count))
        
        generator = SyntheticPatientGenerator()
        rare = generator.generate_rare_combinations(count)
        
        return jsonify({"status": "success", "count": len(rare), "combinations": rare}), 200
    except Exception as e:
        logger.error(f"Error generating rare combinations: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400


@synthetic_bp.route("/edge-cases", methods=["GET"])
@handle_errors
def edge_cases():
    """Generate edge cases for model testing."""
    try:
        generator = SyntheticPatientGenerator()
        cases = generator.generate_edge_cases()
        
        return jsonify({"status": "success", "count": len(cases), "cases": cases}), 200
    except Exception as e:
        logger.error(f"Error generating edge cases: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
