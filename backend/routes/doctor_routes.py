"""
Doctor Dashboard Routes
Provides API endpoints for doctor-facing dashboard with patient overview and risk summary.
Also includes patient dashboard for individual user health tracking.
"""

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from backend import db
from backend.models.patient_history import PatientHistory

doctor_bp = Blueprint("doctor", __name__, template_folder="../templates")


def get_real_dashboard_data():
    """
    Fetch real dashboard data from the PatientHistory table.

    Returns:
        dict: Dashboard metrics and risk distribution data from database
    """
    try:
        # Total predictions (as proxy for patients)
        total_patients = db.session.query(func.count(PatientHistory.id)).scalar() or 0

        # New cases in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        new_cases = (
            db.session.query(func.count(PatientHistory.id))
            .filter(PatientHistory.created_at >= seven_days_ago)
            .scalar()
            or 0
        )

        # Risk distribution counts
        risk_counts = (
            db.session.query(PatientHistory.risk_level, func.count(PatientHistory.id))
            .group_by(PatientHistory.risk_level)
            .all()
        )

        # Initialize counts
        low_risk_count = 0
        medium_risk_count = 0
        high_risk_count = 0
        critical_risk_count = 0

        # Map database results to counts
        for risk_level, count in risk_counts:
            if risk_level == "low":
                low_risk_count = count
            elif risk_level == "medium":
                medium_risk_count = count
            elif risk_level == "high":
                high_risk_count = count
            elif risk_level == "critical":
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

            low_risk_pct, medium_risk_pct, high_risk_pct, critical_risk_pct = (
                base_percentages
            )
        else:
            low_risk_pct = medium_risk_pct = high_risk_pct = critical_risk_pct = 0

        return {
            "total_patients": total_patients,
            "new_cases": new_cases,
            "high_risk_count": high_risk_count,
            "critical_risk_count": critical_risk_count,
            "risk_distribution": {
                "low": {"count": low_risk_count, "percentage": low_risk_pct},
                "medium": {"count": medium_risk_count, "percentage": medium_risk_pct},
                "high": {"count": high_risk_count, "percentage": high_risk_pct},
                "critical": {
                    "count": critical_risk_count,
                    "percentage": critical_risk_pct,
                },
            },
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"⚠️ Error fetching dashboard data: {e}")
        return {
            "total_patients": 0,
            "new_cases": 0,
            "high_risk_count": 0,
            "critical_risk_count": 0,
            "risk_distribution": {
                "low": {"count": 0, "percentage": 0},
                "medium": {"count": 0, "percentage": 0},
                "high": {"count": 0, "percentage": 0},
                "critical": {"count": 0, "percentage": 0},
            },
            "last_updated": datetime.utcnow().isoformat(),
        }


@doctor_bp.route("/doctor-dashboard")
@login_required  # FIX #308: require authentication for doctor dashboard page
def doctor_dashboard():
    """Render the doctor dashboard page"""
    return render_template("doctor_dashboard.html")


@doctor_bp.route("/patient-dashboard")
@login_required
def patient_dashboard():
    """Render the patient dashboard page for authenticated users"""
    return render_template("patient_dashboard.html")


def get_patient_dashboard_data(user_id):
    """
    Fetch dashboard data specific to a patient (user).

    Args:
        user_id: The ID of the currently logged-in user

    Returns:
        dict: Patient-specific dashboard data

    Raises:
        Exception: Propagates database errors to caller for proper handling
    """
    user_predictions = (
        PatientHistory.query.filter_by(user_id=user_id)
        .order_by(PatientHistory.created_at.desc())
        .all()
    )

    total_predictions = len(user_predictions)

    risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    disease_counts = {}

    for pred in user_predictions:
        if pred.risk_level in risk_counts:
            risk_counts[pred.risk_level] += 1
        if pred.disease:
            disease_counts[pred.disease] = disease_counts.get(pred.disease, 0) + 1

    most_common_disease = None
    if disease_counts:
        most_common_disease = max(disease_counts, key=disease_counts.get)

    if total_predictions > 0:
        risk_distribution = {
            level: {
                "count": count,
                "percentage": round((count / total_predictions) * 100, 1),
            }
            for level, count in risk_counts.items()
        }
    else:
        risk_distribution = {
            level: {"count": 0, "percentage": 0} for level in risk_counts
        }

    last_prediction_date = None
    last_disease = None
    if user_predictions:
        last_prediction_date = user_predictions[0].created_at.isoformat()
        last_disease = user_predictions[0].disease

    predictions_list = [pred.to_dict() for pred in user_predictions]

    return {
        "statistics": {
            "total_predictions": total_predictions,
            "high_risk_count": risk_counts["high"],
            "critical_risk_count": risk_counts["critical"],
            "most_common_disease": most_common_disease,
            "last_prediction_date": last_prediction_date,
            "last_disease": last_disease,
        },
        "predictions": predictions_list,
        "risk_distribution": risk_distribution,
        "last_updated": datetime.utcnow().isoformat(),
    }


@doctor_bp.route("/api/patient/dashboard", methods=["GET"])
@login_required
def get_patient_data():
    """
    API endpoint to fetch patient dashboard data for the logged-in user.
    """
    try:
        dashboard_data = get_patient_dashboard_data(current_user.id)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "user_info": {
                            "username": current_user.username,
                            "email": current_user.email,
                        },
                        **dashboard_data,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to fetch patient dashboard data",
                }
            ),
            500,
        )


@doctor_bp.route("/api/patient/temporal-trends", methods=["GET"])
@login_required
def get_patient_temporal_trends():
    """
    API endpoint to fetch sequential patient prediction history and vitals trends.
    """
    try:
        from backend.utils.temporal_analysis import TemporalAnalysisEngine

        user_predictions = (
            PatientHistory.query.filter_by(user_id=current_user.id)
            .order_by(PatientHistory.created_at.asc())
            .all()
        )

        history_list = []
        for pred in user_predictions:
            d = pred.to_dict()
            inputs = d.get("inputs") or {}
            results = d.get("results") or {}

            # Flatten to match what TemporalAnalysisEngine expects
            flat = {
                **d,
                **inputs,
                **results,
                "bayesian_posterior": results.get("bayesian_posterior"),
                "ml_probability": results.get("ml_probability", d.get("probability")),
                "survival_probability": results.get("survival_probability"),
            }
            history_list.append(flat)

        trends = TemporalAnalysisEngine.analyze_history_trends(history_list)

        return jsonify({"success": True, "data": trends}), 200

    except Exception as e:
        import traceback

        traceback.print_exc()
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to process temporal trends analysis",
                }
            ),
            500,
        )


@doctor_bp.route("/api/doctor/dashboard", methods=["GET"])
@login_required  # FIX #308: require authentication for doctor dashboard API
def get_dashboard_data():
    """
    API endpoint to fetch doctor dashboard data from database.
    """
    try:
        dashboard_data = get_real_dashboard_data()

        return jsonify({"success": True, "data": dashboard_data}), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to fetch dashboard data",
                }
            ),
            500,
        )
