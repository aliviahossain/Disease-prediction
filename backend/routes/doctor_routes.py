"""
Doctor Dashboard Routes
Provides API endpoints for doctor-facing dashboard with patient overview and risk summary.
"""

from flask import Blueprint, jsonify, render_template
from datetime import datetime, timedelta
from sqlalchemy import func
from backend import db
from backend.models.prediction import PredictionHistory

doctor_bp = Blueprint(
    'doctor',
    __name__,
    template_folder='../templates'
)


def get_real_dashboard_data():
    """
    Fetch real dashboard data from the PredictionHistory table.
    
    Returns:
        dict: Dashboard metrics and risk distribution data from database
    """
    try:
        # Total predictions (as proxy for patients)
        total_patients = db.session.query(func.count(PredictionHistory.id)).scalar() or 0
        
        # New cases in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        new_cases = db.session.query(func.count(PredictionHistory.id)).filter(
            PredictionHistory.created_at >= seven_days_ago
        ).scalar() or 0
        
        # Risk distribution counts
        risk_counts = db.session.query(
            PredictionHistory.risk_level,
            func.count(PredictionHistory.id)
        ).group_by(PredictionHistory.risk_level).all()
        
        # Initialize counts
        low_risk_count = 0
        medium_risk_count = 0
        high_risk_count = 0
        critical_risk_count = 0
        
        # Map database results to counts
        for risk_level, count in risk_counts:
            if risk_level == 'low':
                low_risk_count = count
            elif risk_level == 'medium':
                medium_risk_count = count
            elif risk_level == 'high':
                high_risk_count = count
            elif risk_level == 'critical':
                critical_risk_count = count
        
        # Calculate percentages (avoid division by zero)
        if total_patients > 0:
            # Compute base integer percentages using floor division
            counts = [
                low_risk_count,
                medium_risk_count,
                high_risk_count,
                critical_risk_count,
            ]
            raw_percentages = [(c * 100.0) / total_patients for c in counts]
            base_percentages = [int(p) for p in raw_percentages]
            remainder = 100 - sum(base_percentages)
            
            # Distribute remaining percentage points to categories with largest fractional parts
            if remainder > 0:
                fractional_parts = [
                    (p - int(p), idx) for idx, p in enumerate(raw_percentages)
                ]
                # Sort by descending fractional part so we add 1% to the largest fractions first
                fractional_parts.sort(reverse=True)
                for i in range(remainder):
                    idx = fractional_parts[i % len(fractional_parts)][1]
                    base_percentages[idx] += 1
            
            low_risk_pct, medium_risk_pct, high_risk_pct, critical_risk_pct = base_percentages
        else:
            low_risk_pct = medium_risk_pct = high_risk_pct = critical_risk_pct = 0
        
        return {
            'total_patients': total_patients,
            'new_cases': new_cases,
            'high_risk_count': high_risk_count,
            'critical_risk_count': critical_risk_count,
            'risk_distribution': {
                'low': {
                    'count': low_risk_count,
                    'percentage': low_risk_pct
                },
                'medium': {
                    'count': medium_risk_count,
                    'percentage': medium_risk_pct
                },
                'high': {
                    'count': high_risk_count,
                    'percentage': high_risk_pct
                },
                'critical': {
                    'count': critical_risk_count,
                    'percentage': critical_risk_pct
                }
            },
            'last_updated': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"⚠️ Error fetching dashboard data: {e}")
        # Return empty data structure on error
        return {
            'total_patients': 0,
            'new_cases': 0,
            'high_risk_count': 0,
            'critical_risk_count': 0,
            'risk_distribution': {
                'low': {'count': 0, 'percentage': 0},
                'medium': {'count': 0, 'percentage': 0},
                'high': {'count': 0, 'percentage': 0},
                'critical': {'count': 0, 'percentage': 0}
            },
            'last_updated': datetime.utcnow().isoformat()
        }


@doctor_bp.route('/doctor-dashboard')
def doctor_dashboard():
    """Render the doctor dashboard page"""
    return render_template('doctor_dashboard.html')


@doctor_bp.route('/patient-dashboard')
def patient_dashboard():
    """Render the patient dashboard placeholder page"""
    return render_template('patient_dashboard.html')


@doctor_bp.route('/api/doctor/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    API endpoint to fetch doctor dashboard data from database.
    
    Returns aggregated patient metrics and risk distribution.
    
    Response JSON:
    {
        "success": true,
        "data": {
            "total_patients": 245,
            "new_cases": 23,
            "high_risk_count": 35,
            "critical_risk_count": 12,
            "risk_distribution": {
                "low": {"count": 120, "percentage": 49},
                "medium": {"count": 78, "percentage": 32},
                "high": {"count": 35, "percentage": 14},
                "critical": {"count": 12, "percentage": 5}
            },
            "last_updated": "2026-01-06T12:00:00"
        }
    }
    """
    try:
        dashboard_data = get_real_dashboard_data()
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch dashboard data'
        }), 500
