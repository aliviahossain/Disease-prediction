"""
backend/utils/uncertainty_handler.py
-------------------------------------
Uncertainty handling for disease predictions.

Prevents overconfident / misleading predictions by checking:
  1. Absolute confidence threshold  — top score must clear the bar.
  2. Margin threshold               — top-1 vs top-2 gap must be wide enough.

Configuration (environment variables):
    PREDICTION_CONFIDENCE_THRESHOLD   default 0.40
    PREDICTION_MARGIN_THRESHOLD       default 0.10

Usage:
    from backend.utils.uncertainty_handler import uncertainty_handler
    check = uncertainty_handler.evaluate(confidence_score=0.32, top2_score=0.28)
    if not check["is_sufficient"]:
        return jsonify(check), 200
"""

from __future__ import annotations
import os

# ── Configurable thresholds ──────────────────────────────────────────────────

CONFIDENCE_THRESHOLD: float = float(
    os.getenv("PREDICTION_CONFIDENCE_THRESHOLD", "0.40")
)
"""
Minimum confidence score required for a prediction to be shown to the user.
Below this value → "Insufficient data" response.
Range: 0.0 – 1.0  |  Recommended: 0.30 – 0.60
"""

MARGIN_THRESHOLD: float = float(os.getenv("PREDICTION_MARGIN_THRESHOLD", "0.10"))
"""
Minimum score gap between the rank-1 and rank-2 prediction.
A near-tie means the model cannot distinguish between two diseases.
Range: 0.0 – 1.0  |  Recommended: 0.05 – 0.15
"""


# ── Main class ───────────────────────────────────────────────────────────────


class UncertaintyHandler:
    """
    Evaluates whether a prediction is confident enough to show the user.

    Parameters
    ----------
    confidence_threshold : float   Absolute minimum for the top score.
    margin_threshold     : float   Minimum gap between top-1 and top-2.
    """

    def __init__(
        self,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        margin_threshold: float = MARGIN_THRESHOLD,
    ) -> None:
        if not (0.0 <= confidence_threshold <= 1.0):
            raise ValueError("confidence_threshold must be in [0.0, 1.0]")
        if not (0.0 <= margin_threshold <= 1.0):
            raise ValueError("margin_threshold must be in [0.0, 1.0]")

        self.confidence_threshold = confidence_threshold
        self.margin_threshold = margin_threshold

    def evaluate(
        self,
        confidence_score: float,
        top2_score: float | None = None,
        disease_name: str = "",
        top2_disease: str = "",
    ) -> dict:
        """
        Decide if the prediction is reliable.

        Parameters
        ----------
        confidence_score : float        Top prediction's confidence (0–1).
        top2_score       : float|None   Second-best score; None if only one result.
        disease_name     : str          Label for the top prediction (for messages).
        top2_disease     : str          Label for the second prediction.

        Returns
        -------
        dict with keys:
            is_sufficient  bool     True → show prediction; False → show warning card.
            reason         str|None Human-readable explanation when False.
            confidence     float    The raw score that was evaluated.
        """
        # ── Input validation ─────────────────────────────────────────────────
        if not (0.0 <= confidence_score <= 1.0):
            raise ValueError(
                f"confidence_score must be in [0.0, 1.0], got {confidence_score}"
            )
        if top2_score is not None and not (0.0 <= top2_score <= 1.0):
            raise ValueError(f"top2_score must be in [0.0, 1.0], got {top2_score}")

        # Check 1 — absolute confidence
        if confidence_score < self.confidence_threshold:
            return {
                "is_sufficient": False,
                "confidence": confidence_score,
                "reason": (
                    f"The model's confidence ({confidence_score:.0%}) is below "
                    f"the minimum threshold ({self.confidence_threshold:.0%}). "
                    "Please provide additional symptoms or diagnostic data for a reliable result."
                ),
            }

        # Check 2 — margin between top-1 and top-2
        if top2_score is not None:
            margin = confidence_score - top2_score
            if margin < self.margin_threshold:
                d1 = disease_name or "condition A"
                d2 = top2_disease or "condition B"
                return {
                    "is_sufficient": False,
                    "confidence": confidence_score,
                    "reason": (
                        f"The model is nearly split between '{d1}' "
                        f"({confidence_score:.0%}) and '{d2}' ({top2_score:.0%}). "
                        f"The {margin:.0%} margin is too small for a reliable prediction. "
                        "More symptoms or test results are needed."
                    ),
                }

        return {"is_sufficient": True, "confidence": confidence_score, "reason": None}

    def get_config(self) -> dict:
        """Return active thresholds (exposed via /api/ml/config)."""
        return {
            "confidence_threshold": self.confidence_threshold,
            "margin_threshold": self.margin_threshold,
        }


# Module-level singleton — import and reuse across all routes
uncertainty_handler = UncertaintyHandler()
