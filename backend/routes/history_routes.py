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
GET    /history/export/csv     Export full prediction history as a CSV file

Fixes the parts of issue #230 that relate to "shown as per need":
the page used to render but its `/api/history` endpoint either didn't
exist or returned an empty list for the wrong user.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from flask import Blueprint, abort, jsonify, make_response, render_template, request
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

# Characters that spreadsheet apps (Excel, Google Sheets, LibreOffice Calc)
# treat as the start of a formula when a cell is opened.
_CSV_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


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


def _sanitize_csv_field(value):
    """
    Neutralize CSV/Formula Injection (CWE-1236).

    User-controlled free-text fields (e.g. disease, notes) are written
    into exported CSVs as-is today. If such a value begins with a
    formula-trigger character, spreadsheet apps interpret it as a
    formula instead of literal text when the file is opened, which can
    lead to data exfiltration or unwanted code execution for whoever
    opens the export (e.g. a doctor the file is shared with).

    Prefixing the value with a single quote forces spreadsheet apps to
    always render it as plain text.
    """
    if value is None:
        return ""
    text = str(value)
    if text.startswith(_CSV_FORMULA_TRIGGERS):
        return "'" + text
    return text


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

    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 20)), 1), 100)
    except ValueError:
        return jsonify(error="Invalid pagination parameters. Must be integers."), 400
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


# --------------------------------------------------------------------- #
# CSV export
# --------------------------------------------------------------------- #
@history_bp.route("/history/export/csv", methods=["GET"])
@login_required
def export_history_csv():
    """Export the current user's full prediction history as a CSV file."""
    user_id = _require_user_id()

    entries = (
        PatientHistory.query
        .filter_by(user_id=user_id)
        .order_by(PatientHistory.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Prediction ID",
        "Prediction Type",
        "Disease",
        "Probability (%)",
        "Risk Level",
        "Inputs",
        "Results",
        "Notes",
        "Created At",
    ])

    for entry in entries:
        writer.writerow([
            entry.id,
            entry.prediction_type or "",
            _sanitize_csv_field(entry.disease),
            round(entry.probability * 100, 2) if entry.probability is not None else "",
            entry.risk_level or "",
            entry.inputs_json or "",
            entry.results_json or "",
            _sanitize_csv_field(entry.notes),
            entry.created_at.strftime("%Y-%m-%d %H:%M:%S") if entry.created_at else "",
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=prediction_history.csv"
    response.headers["Content-Type"] = "text/csv"
    return response