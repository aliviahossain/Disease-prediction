"""
Temporal progression analysis for sequential patient prediction history.

The current disease model scores a single visit. This module layers a small,
deterministic time-series analysis over saved PredictionHistory records so the
application can describe how a patient's risk changes across visits.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional


RISK_SEVERITY = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def _prediction_probability(prediction: Any) -> float:
    probability = prediction.bayesian_posterior
    if probability is None:
        probability = prediction.ml_probability
    return float(probability or 0.0)


def _clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, value))


def _linear_slope(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0

    n = len(values)
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    numerator = sum((idx - mean_x) * (value - mean_y) for idx, value in enumerate(values))
    denominator = sum((idx - mean_x) ** 2 for idx in range(n))
    return numerator / denominator if denominator else 0.0


def _trend_direction(slope: float, delta: float) -> str:
    if slope >= 0.02 or delta >= 0.05:
        return "worsening"
    if slope <= -0.02 or delta <= -0.05:
        return "improving"
    return "stable"


def _weighted_recent_probability(probabilities: List[float], half_life: float = 2.0) -> float:
    if not probabilities:
        return 0.0

    weighted_sum = 0.0
    total_weight = 0.0
    last_index = len(probabilities) - 1

    for index, probability in enumerate(probabilities):
        age = last_index - index
        weight = 0.5 ** (age / half_life)
        weighted_sum += probability * weight
        total_weight += weight

    return weighted_sum / total_weight if total_weight else 0.0


def _risk_transition(previous: Optional[str], current: str) -> str:
    if previous is None:
        return "baseline"

    previous_score = RISK_SEVERITY.get(previous, 0)
    current_score = RISK_SEVERITY.get(current, 0)

    if current_score > previous_score:
        return "escalated"
    if current_score < previous_score:
        return "deescalated"
    return "unchanged"


def analyze_temporal_progression(
    predictions: Iterable[Any],
    disease: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze sequential PredictionHistory records.

    Args:
        predictions: PredictionHistory-like objects.
        disease: Optional disease key used by the caller for filtered histories.

    Returns:
        Dict containing timeline points, trend metrics, weighted recent risk,
        symptom progression, and dynamic probability updates.
    """
    ordered = sorted(
        predictions,
        key=lambda item: item.created_at or datetime.min,
    )

    if not ordered:
        return {
            "disease": disease,
            "observation_count": 0,
            "trend": {
                "direction": "insufficient_data",
                "slope_per_observation": 0.0,
                "probability_delta": 0.0,
                "volatility": 0.0,
            },
            "recent_weighted_probability": 0.0,
            "latest_probability": 0.0,
            "timeline": [],
            "symptom_progression": {
                "new_symptoms": [],
                "resolved_symptoms": [],
                "persistent_symptoms": [],
                "most_frequent_symptoms": [],
            },
            "dynamic_updates": [],
            "interpretation": "Not enough sequential history to assess progression.",
        }

    probabilities = [_prediction_probability(prediction) for prediction in ordered]
    first_probability = probabilities[0]
    latest_probability = probabilities[-1]
    probability_delta = latest_probability - first_probability
    slope = _linear_slope(probabilities)
    direction = _trend_direction(slope, probability_delta)

    deltas = [
        abs(probabilities[index] - probabilities[index - 1])
        for index in range(1, len(probabilities))
    ]
    volatility = sum(deltas) / len(deltas) if deltas else 0.0
    recent_weighted = _weighted_recent_probability(probabilities)

    all_symptoms = [set(prediction.get_symptoms_list()) for prediction in ordered]
    first_symptoms = all_symptoms[0]
    latest_symptoms = all_symptoms[-1]
    symptom_counts = Counter(
        symptom
        for symptom_set in all_symptoms
        for symptom in symptom_set
    )

    timeline = []
    dynamic_updates = []
    previous_probability = None
    previous_risk = None
    running_probabilities: List[float] = []

    for index, prediction in enumerate(ordered):
        probability = probabilities[index]
        running_probabilities.append(probability)
        delta_from_previous = (
            0.0 if previous_probability is None else probability - previous_probability
        )
        risk_transition = _risk_transition(previous_risk, prediction.risk_level)
        symptoms = sorted(all_symptoms[index])

        point = {
            "id": prediction.id,
            "disease": prediction.disease,
            "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
            "probability": round(probability, 4),
            "probability_percent": round(probability * 100, 2),
            "delta_from_previous": round(delta_from_previous, 4),
            "risk_level": prediction.risk_level,
            "risk_transition": risk_transition,
            "symptoms": symptoms,
            "symptom_count": len(symptoms),
        }
        timeline.append(point)

        dynamic_updates.append({
            "created_at": point["created_at"],
            "updated_probability": round(_weighted_recent_probability(running_probabilities), 4),
            "visit_probability": point["probability"],
            "delta_from_previous": point["delta_from_previous"],
            "risk_transition": risk_transition,
        })

        previous_probability = probability
        previous_risk = prediction.risk_level

    symptom_progression = {
        "new_symptoms": sorted(latest_symptoms - first_symptoms),
        "resolved_symptoms": sorted(first_symptoms - latest_symptoms),
        "persistent_symptoms": sorted(first_symptoms & latest_symptoms),
        "most_frequent_symptoms": [
            {"symptom": symptom, "count": count}
            for symptom, count in symptom_counts.most_common(8)
        ],
    }

    if len(ordered) < 2:
        interpretation = "Only one observation is available; collect more history to estimate a trend."
    elif direction == "worsening":
        interpretation = "Recent sequential history suggests increasing predicted risk."
    elif direction == "improving":
        interpretation = "Recent sequential history suggests decreasing predicted risk."
    else:
        interpretation = "Sequential history is relatively stable."

    return {
        "disease": disease,
        "observation_count": len(ordered),
        "trend": {
            "direction": direction if len(ordered) > 1 else "insufficient_data",
            "slope_per_observation": round(slope, 4),
            "probability_delta": round(probability_delta, 4),
            "probability_delta_percent": round(probability_delta * 100, 2),
            "volatility": round(volatility, 4),
        },
        "recent_weighted_probability": round(_clamp_probability(recent_weighted), 4),
        "recent_weighted_probability_percent": round(_clamp_probability(recent_weighted) * 100, 2),
        "latest_probability": round(_clamp_probability(latest_probability), 4),
        "latest_probability_percent": round(_clamp_probability(latest_probability) * 100, 2),
        "timeline": timeline,
        "symptom_progression": symptom_progression,
        "dynamic_updates": dynamic_updates,
        "interpretation": interpretation,
    }
