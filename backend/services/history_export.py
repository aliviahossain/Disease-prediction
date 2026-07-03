"""JSON export for prediction history."""
from datetime import datetime
from backend.models.patient_history import PatientHistory

def export_to_json(user_id):
    entries = PatientHistory.query.filter_by(user_id=user_id).order_by(
        PatientHistory.created_at.desc()).all()
    
    return {
        "user_id": user_id,
        "exported_at": datetime.now().isoformat(),
        "total": len(entries),
        "predictions": [
            {
                "id": e.id,
                "disease": e.disease,
                "probability": float(e.probability) if e.probability else None,
                "risk_level": e.risk_level,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in entries
        ]
    }

