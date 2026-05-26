"""
History service: a single, well-tested entry point that every prediction
route calls when it wants to record a new history entry.

The point of this module is to centralise the "save a prediction" logic
so the calculator route, the image-classifier route, and any future
predictor share exactly one code path. Issue #230 was partly caused by
two routes each having their own (broken) inline save — this fixes that.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Optional

from backend import db
from backend.models.patient_history import PatientHistory

logger = logging.getLogger(__name__)


def _to_json(value: Any) -> Optional[str]:
    """Best-effort JSON serialisation. Returns None on failure."""
    if value is None:
        return None
    try:
        return json.dumps(value, default=str, sort_keys=True)
    except (TypeError, ValueError) as exc:
        logger.warning("history.save: could not serialise value: %s", exc)
        return None


def _classify_risk(probability: Optional[float]) -> Optional[str]:
    """Map a probability to a coarse risk band (low / medium / high)."""
    if probability is None:
        return None
    try:
        p = float(probability)
    except (TypeError, ValueError):
        return None
    if p < 0.30:
        return "low"
    if p < 0.70:
        return "medium"
    return "high"


def save_history(
    user_id: Optional[int],
    *,
    prediction_type: str,
    disease: Optional[str] = None,
    inputs: Optional[Mapping[str, Any]] = None,
    results: Optional[Mapping[str, Any]] = None,
    probability: Optional[float] = None,
    risk_level: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[PatientHistory]:
    """Persist a single PatientHistory row.

    Returns the created entry, or None if the user is anonymous or if
    the database write fails. Anonymous users (no `user_id`) are silently
    skipped — the calling route should still return its normal response
    so the prediction itself isn't blocked behind login.

    This function deliberately never raises: a failure to record history
    must not break the user's prediction. Errors are logged.
    """
    if not user_id:
        # Anonymous user — nothing to save, but not an error.
        return None

    if not prediction_type:
        logger.warning("history.save called without prediction_type; skipping")
        return None

    try:
        probability_value = float(probability) if probability is not None else None
    except (TypeError, ValueError):
        logger.warning(
            "history.save: invalid probability value %r; storing as None",
            probability,
        )
        probability_value = None

    entry = PatientHistory(
        user_id=user_id,
        prediction_type=prediction_type[:32],
        disease=(disease or "")[:120] or None,
        inputs_json=_to_json(inputs),
        results_json=_to_json(results),
        probability=probability_value,
        risk_level=risk_level or _classify_risk(probability_value),
        notes=(notes or "")[:2000] or None,
    )

    try:
        db.session.add(entry)
        db.session.commit()
        logger.info(
            "history.save: stored entry id=%s for user_id=%s type=%s",
            entry.id,
            user_id,
            prediction_type,
        )
        return entry
    except Exception as exc:  # broad on purpose — see docstring
        logger.exception("history.save: failed to persist history entry: %s", exc)
        db.session.rollback()
        return None
