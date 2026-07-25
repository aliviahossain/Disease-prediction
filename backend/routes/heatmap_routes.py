from flask import Blueprint, jsonify, render_template
from backend.models.ml_model import ml_model
import json  # noqa

heatmap_bp = Blueprint("heatmap", __name__)


@heatmap_bp.route("/model-explorer")
def model_explorer_page():
    """Render the model explorer page with heatmap visualization."""
    return render_template("model_explorer.html")


@heatmap_bp.route("/api/model/correlations")
def get_correlations():
    """
    Get P(symptom|disease) correlation matrix for heatmap.

    Returns JSON with structure:
    {
      "diseases": ["diabetes", "fever", ...],
      "symptoms": ["fever", "cough", ...],
      "matrix": [[0.85, 0.22, ...], ...]
    }
    """
    diseases = ml_model.get_available_diseases()
    symptoms = ml_model.get_all_unique_symptoms()

    # Build correlation matrix
    matrix = []
    for disease in diseases:
        row = []
        for symptom in symptoms:
            prob = ml_model.P(symptom["key"], disease, given_disease=True)
            row.append(round(prob, 3))
        matrix.append(row)

    return jsonify(
        {
            "diseases": [d.replace("_", " ").title() for d in diseases],
            "symptoms": [s["label"] for s in symptoms],
            "matrix": matrix,
            "metadata": {
                "total_diseases": len(diseases),
                "total_symptoms": len(symptoms),
                "data_source": "model.parameters",
            },
        }
    )
