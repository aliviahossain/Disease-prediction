"""
Tests for Doctor Dashboard functionality.
Tests database persistence, data aggregation, percentage calculations, and error handling.  # noqa: E501
"""

import json
from datetime import datetime

import pytest

from backend import create_app, db
from backend.models.patient_history import PatientHistory
from backend.models.user import User


@pytest.fixture
def app():
    """Create and configure a test application instance with an isolated SQLite DB."""  # noqa: E501
    import os
    import tempfile
    import time

    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(db_fd)

    os.environ["SECRET_KEY"] = "test-secret-key-not-for-prod"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()

    for attempt in range(10):
        try:
            os.unlink(db_path)
            break
        except PermissionError:
            time.sleep(0.1)


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a real user for authenticated dashboard tests."""
    with app.app_context():
        user = User(
            username="doctor_test_user",
            email="doctor@example.com",
            password_hash="test-password-hash",
        )
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def auth_client(client, test_user):
    """Create an authenticated test client."""
    with client.session_transaction() as session:
        session["_user_id"] = str(test_user)
        session["_fresh"] = True
    return client


@pytest.fixture
def sample_predictions(app, test_user):
    """Create sample predictions in the database."""
    with app.app_context():
        predictions = [
            PatientHistory(
                user_id=test_user,
                prediction_type="symptom",
                disease="diabetes",
                inputs_json=json.dumps(
                    {"symptoms": ["fatigue", "increased_thirst"], "age": 35}
                ),
                results_json=json.dumps(
                    {"ml_probability": 0.25, "bayesian_posterior": 0.30}
                ),
                probability=0.30,
                risk_level="low",
                created_at=datetime.utcnow(),
            ),
            PatientHistory(
                user_id=test_user,
                prediction_type="symptom",
                disease="hypertension",
                inputs_json=json.dumps(
                    {"symptoms": ["headache", "dizziness"], "age": 45}
                ),
                results_json=json.dumps(
                    {"ml_probability": 0.55, "bayesian_posterior": 0.60}
                ),
                probability=0.60,
                risk_level="medium",
                created_at=datetime.utcnow(),
            ),
            PatientHistory(
                user_id=test_user,
                prediction_type="symptom",
                disease="heart_disease",
                inputs_json=json.dumps(
                    {"symptoms": ["chest_pain", "shortness_breath"], "age": 55}
                ),
                results_json=json.dumps(
                    {"ml_probability": 0.75, "bayesian_posterior": 0.80}
                ),
                probability=0.80,
                risk_level="high",
                created_at=datetime.utcnow(),
            ),
            PatientHistory(
                user_id=test_user,
                prediction_type="symptom",
                disease="covid19",
                inputs_json=json.dumps(
                    {
                        "symptoms": ["fever", "cough", "loss_taste_smell"],
                        "age": 65,
                    }
                ),
                results_json=json.dumps(
                    {"ml_probability": 0.90, "bayesian_posterior": 0.95}
                ),
                probability=0.95,
                risk_level="critical",
                created_at=datetime.utcnow(),
            ),
        ]

        for pred in predictions:
            db.session.add(pred)
        db.session.commit()

        yield predictions


class TestDoctorDashboardAPI:
    """Tests for the Doctor Dashboard API endpoint."""

    def test_dashboard_returns_success(self, auth_client, sample_predictions):
        """Test that dashboard API returns success status."""
        response = auth_client.get("/api/doctor/dashboard")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_dashboard_returns_correct_total_patients(
        self, auth_client, sample_predictions
    ):
        """Test that dashboard returns correct total patient count."""
        response = auth_client.get("/api/doctor/dashboard")
        data = json.loads(response.data)
        assert data["data"]["total_patients"] == 4

    def test_dashboard_returns_correct_risk_distribution(
        self, auth_client, sample_predictions
    ):
        """Test that dashboard returns correct risk distribution counts."""
        response = auth_client.get("/api/doctor/dashboard")
        data = json.loads(response.data)

        risk_dist = data["data"]["risk_distribution"]
        assert risk_dist["low"]["count"] == 1
        assert risk_dist["medium"]["count"] == 1
        assert risk_dist["high"]["count"] == 1
        assert risk_dist["critical"]["count"] == 1

    def test_dashboard_percentages_sum_to_100(
        self, auth_client, sample_predictions
    ):
        """Test that risk percentages sum to exactly 100%."""
        response = auth_client.get("/api/doctor/dashboard")
        data = json.loads(response.data)

        risk_dist = data["data"]["risk_distribution"]
        total_pct = (
            risk_dist["low"]["percentage"]
            + risk_dist["medium"]["percentage"]
            + risk_dist["high"]["percentage"]
            + risk_dist["critical"]["percentage"]
        )
        assert total_pct == 100

    def test_dashboard_empty_database(self, auth_client, app):
        """Test dashboard with empty database."""
        response = auth_client.get("/api/doctor/dashboard")
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["total_patients"] == 0
        assert data["data"]["new_cases"] == 0

    def test_dashboard_new_cases_count(self, auth_client, sample_predictions):
        """Test that new cases (last 7 days) are counted correctly."""
        response = auth_client.get("/api/doctor/dashboard")
        data = json.loads(response.data)

        # All sample predictions were created now, so they should be in new_cases # noqa: E501
        assert data["data"]["new_cases"] == 4

    def test_dashboard_high_risk_count(self, auth_client, sample_predictions):
        """Test that high risk count is correct."""
        response = auth_client.get("/api/doctor/dashboard")
        data = json.loads(response.data)

        assert data["data"]["high_risk_count"] == 1

    def test_dashboard_critical_risk_count(
        self, auth_client, sample_predictions
    ):
        """Test that critical risk count is correct."""
        response = auth_client.get("/api/doctor/dashboard")
        data = json.loads(response.data)

        assert data["data"]["critical_risk_count"] == 1


class TestPredictionPersistence:
    """Tests for prediction persistence in the ML predict endpoint."""

    def test_prediction_saved_to_database(self, auth_client, app):
        """Test that predictions are saved to the database."""
        payload = {
            "disease": "diabetes",
            "symptoms": ["increased_thirst", "frequent_urination", "fatigue"],
            "age": 45,
        }

        response = auth_client.post(
            "/api/ml/predict",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200

        with app.app_context():
            predictions = PatientHistory.query.all()
            assert len(predictions) == 1
            assert predictions[0].disease == "Diabetes"
            inputs = json.loads(predictions[0].inputs_json)
            assert inputs.get("age") == 45

    def test_prediction_risk_level_saved(self, auth_client, app):
        """Test that risk level is correctly saved based on probability."""
        payload = {
            "disease": "diabetes",
            "symptoms": [
                "increased_thirst",
                "frequent_urination",
                "fatigue",
                "blurred_vision",
            ],
            "age": 55,
        }

        response = auth_client.post(
            "/api/ml/predict",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200

        with app.app_context():
            prediction = PatientHistory.query.first()
            assert prediction.risk_level in [
                "low",
                "medium",
                "high",
                "critical",
            ]

    def test_prediction_symptoms_stored_as_json(self, auth_client, app):
        """Test that symptoms are stored as JSON string."""
        payload = {
            "disease": "diabetes",
            "symptoms": ["increased_thirst", "frequent_urination", "fatigue"],
            "age": 40,
        }

        auth_client.post(
            "/api/ml/predict",
            data=json.dumps(payload),
            content_type="application/json",
        )

        with app.app_context():
            prediction = PatientHistory.query.first()
            inputs = json.loads(prediction.inputs_json)
            assert "increased_thirst" in inputs["symptoms"]
            assert "frequent_urination" in inputs["symptoms"]


class TestDoctorDashboardPage:
    """Tests for the Doctor Dashboard page rendering."""

    def test_dashboard_page_loads(self, auth_client):
        """Test that doctor dashboard page loads successfully."""
        response = auth_client.get("/doctor-dashboard")
        assert response.status_code == 200

    def test_patient_dashboard_requires_login(self, client):
        """Test that patient dashboard redirects unauthenticated users to login."""  # noqa: E501
        response = client.get("/patient-dashboard")
        # Should redirect to login page
        assert response.status_code == 302
