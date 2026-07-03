"""
JSON export functionality for prediction history.

Extends CSV export with structured JSON format.
"""

from flask import Blueprint, request, jsonify, make_response
from flask_login import login_required
from backend.models.patient_history import PatientHistory

def export_history_json(user_id: int) -> dict:
    """Export user's full prediction history as JSON."""
    entries = (
        PatientHistory.query
        .filter_by(user_id=user_id)
        .order_by(PatientHistory.created_at.desc())
        .all()
    )
    
    return {
        "user_id": user_id,
        "exported_at": datetime.now().isoformat(),
        "total_predictions": len(entries),
        "predictions": [
            {
                "id": e.id,
                "prediction_type": e.prediction_type,
                "disease": e.disease,
                "probability": float(e.probability) if e.probability else None,
                "risk_level": e.risk_level,
                "inputs": json.loads(e.inputs_json) if e.inputs_json else {},
                "results": json.loads(e.results_json) if e.results_json else {},
                "notes": e.notes,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in entries
        ]
    }

