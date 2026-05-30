"""
History routes — page and JSON API.

Endpoints
---------
GET    /history                Page: renders history.html
GET    /api/history            JSON list of current user's history (paginated)
GET    /api/history/<id>       JSON detail for a single entry
DELETE /api/history/<id>       Delete a single entry (owned by current user)
DELETE /api/history            Clear ALL of the current user's history
POST   /api/history            Manually add an entry (used by older
                                client code that still POSTs from the
                                browser instead of going through a
                                prediction route)

Fixes the parts of issue #230 that relate to "shown as per need":
the page used to render but its `/api/history` endpoint either didn't
exist or returned an empty list for the wrong user.
"""

from __future__ import annotations

import logging
from typing import Optional

from flask import (
    Blueprint, jsonify, render_template, request, abort, current_app,
)
from flask_login import current_user, login_required

from backend import db
from backend.models.patient_history import PatientHistory
from backend.services.history_service import save_history
from backend.middleware.error_handler import UnauthorizedError

logger = logging.getLogger(__name__)

history_bp = Blueprint(
    "history",
    __name__,
    template_folder="../templates",
)


# --------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------- #
def _require_user_id() -> int:
    """Return the current authenticated user's id, or raise UnauthorizedError."""
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
    """Render the History page. The list itself is fetched async by JS."""
    return render_template("history.html")


# --------------------------------------------------------------------- #
# JSON API
# --------------------------------------------------------------------- #
@history_bp.route("/api/history", methods=["GET"])
def list_history():
    """Return current user's history, newest first, with pagination.

    Query params:
        page  (int, default 1)
        per_page (int, default 20, capped at 100)
        type  (optional: filter by prediction_type)
    """
    user_id = _require_user_id()

    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 20)), 1), 100)
    except ValueError:
        return jsonify(error="Invalid pagination parameters. Must be integers."), 400
    type_filter: Optional[str] = request.args.get("type") or None

    query = (
        PatientHistory.query
        .filter_by(user_id=user_id)
        .order_by(PatientHistory.created_at.desc())
    )
    if type_filter:
        query = query.filter_by(prediction_type=type_filter)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [entry.to_dict() for entry in paginated.items],
        "page": paginated.page,
        "per_page": paginated.per_page,
        "total": paginated.total,
        "pages": paginated.pages,
        "has_next": paginated.has_next,
        "has_prev": paginated.has_prev,
    })


@history_bp.route("/api/history/<int:entry_id>", methods=["GET"])
def get_history_entry(entry_id: int):
    """Return one entry, 404 if it belongs to someone else."""
    entry = _get_or_404(entry_id)
    return jsonify(entry.to_dict())


@history_bp.route("/api/history/<int:entry_id>", methods=["DELETE"])
def delete_history_entry(entry_id: int):
    """Delete a single entry owned by the current user."""
    entry = _get_or_404(entry_id)
    try:
        db.session.delete(entry)
        db.session.commit()
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to delete history entry %s", entry_id)
        db.session.rollback()
        return jsonify(error="delete_failed"), 500
    return jsonify(ok=True, deleted_id=entry_id)


@history_bp.route("/api/history", methods=["DELETE"])
def clear_history():
    """Delete ALL of the current user's history. Irreversible."""
    user_id = _require_user_id()
    deleted = (
        PatientHistory.query
        .filter_by(user_id=user_id)
        .delete(synchronize_session=False)
    )
    try:
        db.session.commit()
    except Exception:  # pragma: no cover
        logger.exception("Failed to clear history for user %s", user_id)
        db.session.rollback()
        return jsonify(error="clear_failed"), 500
    return jsonify(ok=True, deleted_count=deleted)


@history_bp.route("/api/history", methods=["POST"])
def add_history_entry():
    """
    Manual save endpoint.

    The recommended path is for prediction routes to call
    `save_history(...)` directly (see backend/services/history_service.py).
    This POST endpoint exists so older frontend code that explicitly
    POSTs after rendering a result keeps working — it's the second half
    of fixing the "not being recorded" bug.
    """
    user_id = _require_user_id()
    payload = request.get_json(silent=True) or {}

    entry = save_history(
        user_id=user_id,
        prediction_type=payload.get("prediction_type", "bayes"),
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