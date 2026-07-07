import math
from typing import List, Dict


def calculate_symptom_contributions(
    symptoms: List[str], disease: str, model
) -> List[Dict]:
    """Calculate log-odds contribution of each symptom."""
    contributions = []
    for symptom in symptoms:
        p_symp_disease = model.P(symptom, disease, given_disease=True)
        p_symp_no_disease = model.P(symptom, disease, given_disease=False)

        if p_symp_no_disease < 1e-10:
            p_symp_no_disease = 1e-10

        lr = p_symp_disease / p_symp_no_disease
        log_odds = math.log(lr) if lr > 0 else 0

        contributions.append(
            {
                "symptom": symptom,
                "log_odds": round(log_odds, 4),
                "direction": "positive" if lr > 1 else "negative",
            }
        )

    total = sum(abs(c["log_odds"]) for c in contributions)
    if total > 0:
        for c in contributions:
            c["contribution_pct"] = round(abs(c["log_odds"]) / total * 100, 1)
    else:
        for c in contributions:
            c["contribution_pct"] = 0

    return sorted(contributions, key=lambda x: -x["contribution_pct"])
