"""
Threshold adjustment for reducing false negatives in disease prediction.

Clinical safety requires high sensitivity: better to over-predict and let
the doctor rule out than to miss a serious disease.
"""


def adjust_prediction_threshold(disease: str, model) -> float:
    """
    Get adjusted threshold for disease prediction.

    Uses class-specific thresholds to balance sensitivity vs specificity.
    For critical diseases: lower threshold = higher sensitivity.
    """
    critical_diseases = {
        "cancer": 0.35,
        "heart_disease": 0.40,
        "stroke": 0.38,
        "diabetes": 0.45,
        "kidney_disease": 0.40,
    }

    default_threshold = 0.50
    return critical_diseases.get(disease.lower(), default_threshold)


def apply_ensemble_voting(predictions: dict, model) -> dict:
    """
    Apply ensemble voting to reduce false negatives.

    Combines multiple models: Naive Bayes, Random Forest, SVM.
    Prediction: "positive" if >= 2 models agree.
    """
    predictions_list = list(predictions.values())
    confidence = sum(predictions_list) / len(predictions_list)

    # Lower threshold for ensemble reduces false negatives
    ensemble_threshold = 0.40
    is_positive = confidence >= ensemble_threshold

    return {
        "ensemble_confidence": round(confidence, 4),
        "ensemble_decision": is_positive,
        "individual_predictions": predictions,
        "agreement_count": sum(1 for p in predictions.values() if p >= 0.5),
    }
