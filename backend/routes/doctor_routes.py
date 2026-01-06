"""
Doctor Dashboard Routes
Provides API endpoints for doctor-facing dashboard with patient overview and risk summary.
"""

from flask import Blueprint, jsonify, render_template
from datetime import datetime, timedelta
import random

doctor_bp = Blueprint(
    'doctor',
    __name__,
    template_folder='../templates'
)


def get_mock_dashboard_data():
    """
    Generate mock dashboard data for demonstration.
    In production, this would query actual patient/prediction records from the database.
    
    Returns:
        dict: Dashboard metrics and risk distribution data
    """
    # Mock patient counts - in production, query from database
    total_patients = random.randint(150, 300)
    new_cases_7_days = random.randint(10, 35)
    
    # Risk distribution (percentages should sum to 100)
    low_risk_pct = random.randint(40, 55)
    medium_risk_pct = random.randint(20, 30)
    high_risk_pct = random.randint(10, 20)
    critical_risk_pct = 100 - low_risk_pct - medium_risk_pct - high_risk_pct
    
    # Calculate actual counts from percentages
    low_risk_count = int(total_patients * low_risk_pct / 100)
    medium_risk_count = int(total_patients * medium_risk_pct / 100)
    high_risk_count = int(total_patients * high_risk_pct / 100)
    critical_risk_count = total_patients - low_risk_count - medium_risk_count - high_risk_count
    
    return {
        'total_patients': total_patients,
        'new_cases': new_cases_7_days,
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
    API endpoint to fetch doctor dashboard data.
    
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
        dashboard_data = get_mock_dashboard_data()
        
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
