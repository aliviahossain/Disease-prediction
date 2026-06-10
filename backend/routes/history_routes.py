from __future__ import annotations

import logging
from typing import Optional

from flask import Blueprint, abort, jsonify, render_template, request
from flask_login import current_user, login_required

from backend import db
from backend.middleware.error_handler import UnauthorizedError
from backend.models.patient_history import PatientHistory
from backend.services.history_service import save_history

logger = logging.getLogger(__name__)

history_bp = Blueprint(
    "history",
    __name__,
    template_folder="../templates",
)

# ---------------------------------------------------------------------------
# Security constants
# ---------------------------------------------------------------------------
ALLOWED_PREDICTION_TYPES = {"bayes", "ml"}


# --------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------- #
def _require_user_id() -> int:
    if not current_user.is_authenticated:
        raise UnauthorizedError("You must be logged in to view history.")
    return current_user.id


def _get_or_404(entry_id: int) -> PatientHistory:
    entry = PatientHistory.query.get(entry_id)
    if entry is None or entry.user_id != _require_user_id():
        abort(404)
    return entry


# --------------------------------------------------------------------- #
# HTML page
# --------------------------------------------------------------------- #
@history_bp.route("/history", methods=["GET"])
@login_required
def history_page():
    return render_template("history.html")


# --------------------------------------------------------------------- #
# JSON API
# --------------------------------------------------------------------- #
@history_bp.route("/api/history", methods=["GET"])
def list_history():
    user_id = _require_user_id()

    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 20)), 1), 100)
    type_filter: Optional[str] = request.args.get("type") or None

    query = PatientHistory.query.filter_by(user_id=user_id).order_by(
        PatientHistory.created_at.desc()
    )
    if type_filter:
        query = query.filter_by(prediction_type=type_filter)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "items": [entry.to_dict() for entry in paginated.items],
            "page": paginated.page,
            "per_page": paginated.per_page,
            "total": paginated.total,
            "pages": paginated.pages,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
        }
    )


@history_bp.route("/api/history/<int:entry_id>", methods=["GET"])
def get_history_entry(entry_id: int):
    entry = _get_or_404(entry_id)
    return jsonify(entry.to_dict())


@history_bp.route("/api/history/<int:entry_id>", methods=["DELETE"])
def delete_history_entry(entry_id: int):
    entry = _get_or_404(entry_id)
    try:
        db.session.delete(entry)
        db.session.commit()
    except Exception:
        logger.exception("Failed to delete history entry %s", entry_id)
        db.session.rollback()
        return jsonify(error="delete_failed"), 500
    return jsonify(ok=True, deleted_id=entry_id)


@history_bp.route("/api/history", methods=["DELETE"])
def clear_history():
    user_id = _require_user_id()
    deleted = PatientHistory.query.filter_by(user_id=user_id).delete(
        synchronize_session=False
    )
    try:
        db.session.commit()
    except Exception:
        logger.exception("Failed to clear history for user %s", user_id)
        db.session.rollback()
        return jsonify(error="clear_failed"), 500
    return jsonify(ok=True, deleted_count=deleted)


@history_bp.route("/api/history", methods=["POST"])
def add_history_entry():
    user_id = _require_user_id()
    payload = request.get_json(silent=True) or {}

    prediction_type = payload.get("prediction_type", "bayes")
    if prediction_type not in ALLOWED_PREDICTION_TYPES:
        return jsonify(
            error=f"Invalid prediction_type. Allowed values: {', '.join(sorted(ALLOWED_PREDICTION_TYPES))}"
        ), 400

    entry = save_history(
        user_id=user_id,
        prediction_type=prediction_type,
        disease=payload.get("disease"),
        inputs=payload.get("inputs"),
        results=payload.get("results"),
        probability=payload.get("probability"),
        risk_level=payload.get("risk_level"),
        notes=payload.get("notes"),
    )
    if entry is None:
        return jsonify(error="save_failed"), 500
    return jsonify(entry.to_dict()), 201