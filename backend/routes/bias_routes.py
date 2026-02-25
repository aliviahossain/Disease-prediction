"""
Routes for Dataset Bias & Coverage Analysis Dashboard.
"""

from flask import Blueprint, render_template, jsonify
import logging

logger = logging.getLogger(__name__)

bias_bp = Blueprint('bias', __name__)


@bias_bp.route('/bias-analysis')
def bias_dashboard():
    """Render the bias analysis dashboard page."""
    return render_template('bias_dashboard.html')


@bias_bp.route('/api/bias-analysis')
def bias_analysis_api():
    """
    API endpoint that returns the full bias analysis as JSON.
    Used by the dashboard frontend to populate charts and tables.
    """
    try:
        from backend.analysis.bias_analysis import get_analyzer
        analyzer = get_analyzer()
        analysis = analyzer.run_full_analysis()
        return jsonify({'success': True, 'data': analysis})
    except Exception as e:
        logger.error(f"Bias analysis failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
