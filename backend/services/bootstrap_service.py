import numpy as np
from typing import Dict, List

def compute_confidence_interval(
    symptoms: List[str],
    model,
    n_bootstrap: int = 1000,
    alpha: float = 0.05
) -> Dict:
    """
    Compute 95% confidence interval using bootstrap resampling.
    
    Returns {point, lower, upper, confidence_level}
    """
    predictions = []
    
    for _ in range(n_bootstrap):
        # Resample posterior estimate
        p = model.predict_disease_probability_bootstrap(symptoms)
        predictions.append(p)
    
    predictions = np.array(predictions)
    point = np.mean(predictions)
    lower = np.percentile(predictions, 100 * alpha / 2)
    upper = np.percentile(predictions, 100 * (1 - alpha / 2))
    
    interval_width = upper - lower
    if interval_width < 0.10:
        confidence_level = "High Confidence"
    elif interval_width < 0.25:
        confidence_level = "Moderate Confidence"
    else:
        confidence_level = "Low Confidence"
    
    return {
        "point": round(point, 4),
        "lower": round(lower, 4),
        "upper": round(upper, 4),
        "interval_width": round(interval_width, 4),
        "confidence_level": confidence_level
    }

