from flask import Blueprint, request, jsonify
from rapidfuzz import fuzz
from backend.models.ml_model import ml_model

autocomplete_bp = Blueprint("autocomplete", __name__)


@autocomplete_bp.route("/api/symptoms/search", methods=["GET"])
def search_symptoms():
    """Fuzzy search for symptoms with ranking."""
    query = request.args.get("q", "").strip().lower()
    limit = min(int(request.args.get("limit", 8)), 50)

    if len(query) < 2:
        return jsonify([])

    all_symptoms = ml_model.get_all_unique_symptoms()
    matches = []
    for symptom in all_symptoms:
        label = symptom.get("label", symptom.get("key", "")).lower()
        score = fuzz.token_set_ratio(query, label)
        if score > 40:
            matches.append(
                {
                    "id": symptom.get("key"),
                    "label": symptom.get("label", symptom.get("key")),
                    "score": score,
                }
            )

    ranked = sorted(matches, key=lambda x: -x["score"])[:limit]
    return jsonify(ranked)
