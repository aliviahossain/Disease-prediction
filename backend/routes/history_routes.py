from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from backend.models.prediction import PredictionHistory
from backend import db

history_bp = Blueprint('history', __name__)

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
