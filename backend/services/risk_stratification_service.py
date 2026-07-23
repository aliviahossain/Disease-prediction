from enum import Enum
from typing import Dict


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def stratify_risk(
    probability: float,
    age: int = None,
    comorbidities: list = None,
) -> Dict:
    """
    Stratify patient risk and provide personalized recommendations.

    Returns {risk_level, score, factors, recommendations}
    """
    score = probability * 100
    factors = []

    # Base probability risk
    if score >= 80:
        base_risk = RiskLevel.CRITICAL
    elif score >= 60:
        base_risk = RiskLevel.HIGH
    elif score >= 40:
        base_risk = RiskLevel.MEDIUM
    else:
        base_risk = RiskLevel.LOW  # noqa

    # Age factor
    age_factor = 0
    if age and age > 60:
        age_factor = 10
        factors.append("Age > 60 years")
    elif age and age > 75:
        age_factor = 15
        factors.append("Age > 75 years (high risk)")

    # Comorbidity factor
    comorbidity_factor = 0
    if comorbidities:
        comorbidity_factor = min(len(comorbidities) * 5, 20)
        factors.append(f"{len(comorbidities)} comorbidities")

    adjusted_score = min(score + age_factor + comorbidity_factor, 100)

    # Determine final risk level
    if adjusted_score >= 80:
        final_risk = RiskLevel.CRITICAL
    elif adjusted_score >= 60:
        final_risk = RiskLevel.HIGH
    elif adjusted_score >= 40:
        final_risk = RiskLevel.MEDIUM
    else:
        final_risk = RiskLevel.LOW

    # Recommendations
    recommendations = {
        RiskLevel.CRITICAL: [
            "Immediate medical consultation required",
            "Consider hospitalization",
        ],
        RiskLevel.HIGH: [
            "Schedule urgent appointment with specialist",
            "Monitor symptoms closely",
        ],
        RiskLevel.MEDIUM: [
            "Schedule appointment with healthcare provider",
            "Lifestyle modifications recommended",
        ],
        RiskLevel.LOW: [
            "Continue regular health checkups",
            "Maintain healthy lifestyle",
        ],
    }

    return {
        "risk_level": final_risk.value,
        "risk_score": round(adjusted_score, 1),
        "probability": round(probability * 100, 1),
        "risk_factors": factors,
        "recommendations": recommendations[final_risk],
        "prognosis": f"Based on current factors, monitoring and {recommendations[final_risk][0].lower()}",  # noqa: E501
    }
