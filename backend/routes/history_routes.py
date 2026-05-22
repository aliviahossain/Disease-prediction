from flask import Blueprint, render_template, abort, Response
from flask_login import login_required, current_user
from backend.models.prediction import PredictionHistory
from backend import db
import logging
import csv
from io import StringIO

history_bp = Blueprint('history', __name__)
logger = logging.getLogger(__name__)

@history_bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """
    Fetch and display the prediction history for the current user.
    Ordered by creation date descending (newest first).
    """
    # Query logic to fetch user-specific data
    history = (
        PredictionHistory.query.filter_by(user_id=current_user.id)
        .order_by(PredictionHistory.created_at.desc())
        .all()
    )

    return render_template('history.html', history=history)


@history_bp.route('/history/<int:prediction_id>', methods=['GET'])
@login_required
def history_detail(prediction_id):
    """
    Display detailed information for a single prediction history record.
    Ensures the record belongs to the current user.
    """
    prediction = (
        PredictionHistory.query.filter_by(id=prediction_id, user_id=current_user.id)
        .first_or_404()
    )

    return render_template('history_detail.html', prediction=prediction)

@history_bp.route('/history/export/csv', methods=['GET'])
@login_required
def export_history_csv():
    """
    Export prediction history as CSV for the current user.
    """

    history = (
        PredictionHistory.query.filter_by(user_id=current_user.id)
        .order_by(PredictionHistory.created_at.desc())
        .all()
    )

    output = StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow([
        'Prediction ID',
        'Disease',
        'Risk Level',
        'Created At'
    ])

    # CSV Rows
    for record in history:
        writer.writerow([
            record.id,
            record.disease,
            record.risk_level,
            record.created_at
        ])

    output.seek(0)

    try:
        return Response(
            output,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=prediction_history.csv'
            }
        )

    except Exception:
        logger.exception(
            "Failed to export prediction history for user_id=%s",
            current_user.id
        )

        abort(500)
