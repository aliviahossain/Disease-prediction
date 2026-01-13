"""
Tests for Doctor Dashboard functionality.
Tests database persistence, data aggregation, percentage calculations, and error handling.
"""

import pytest
import json
from datetime import datetime, timedelta
from backend import create_app, db
from backend.models.prediction import PredictionHistory


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def sample_predictions(app):
    """Create sample predictions in the database."""
    with app.app_context():
        predictions = [
            PredictionHistory(
                disease='diabetes',
                symptoms=json.dumps(['fatigue', 'increased_thirst']),
                ml_probability=0.25,
                bayesian_posterior=0.30,
                risk_level='low',
                patient_age=35,
                created_at=datetime.utcnow()
            ),
            PredictionHistory(
                disease='hypertension',
                symptoms=json.dumps(['headache', 'dizziness']),
                ml_probability=0.55,
                bayesian_posterior=0.60,
                risk_level='medium',
                patient_age=45,
                created_at=datetime.utcnow()
            ),
            PredictionHistory(
                disease='heart_disease',
                symptoms=json.dumps(['chest_pain', 'shortness_breath']),
                ml_probability=0.75,
                bayesian_posterior=0.80,
                risk_level='high',
                patient_age=55,
                created_at=datetime.utcnow()
            ),
            PredictionHistory(
                disease='covid19',
                symptoms=json.dumps(['fever', 'cough', 'loss_taste_smell']),
                ml_probability=0.90,
                bayesian_posterior=0.95,
                risk_level='critical',
                patient_age=65,
                created_at=datetime.utcnow()
            ),
        ]
        
        for pred in predictions:
            db.session.add(pred)
        db.session.commit()
        
        yield predictions


class TestDoctorDashboardAPI:
    """Tests for the Doctor Dashboard API endpoint."""
    
    def test_dashboard_returns_success(self, client, sample_predictions):
        """Test that dashboard API returns success status."""
        response = client.get('/api/doctor/dashboard')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_dashboard_returns_correct_total_patients(self, client, sample_predictions):
        """Test that dashboard returns correct total patient count."""
        response = client.get('/api/doctor/dashboard')
        data = json.loads(response.data)
        assert data['data']['total_patients'] == 4
    
    def test_dashboard_returns_correct_risk_distribution(self, client, sample_predictions):
        """Test that dashboard returns correct risk distribution counts."""
        response = client.get('/api/doctor/dashboard')
        data = json.loads(response.data)
        
        risk_dist = data['data']['risk_distribution']
        assert risk_dist['low']['count'] == 1
        assert risk_dist['medium']['count'] == 1
        assert risk_dist['high']['count'] == 1
        assert risk_dist['critical']['count'] == 1
    
    def test_dashboard_percentages_sum_to_100(self, client, sample_predictions):
        """Test that risk percentages sum to exactly 100%."""
        response = client.get('/api/doctor/dashboard')
        data = json.loads(response.data)
        
        risk_dist = data['data']['risk_distribution']
        total_pct = (
            risk_dist['low']['percentage'] +
            risk_dist['medium']['percentage'] +
            risk_dist['high']['percentage'] +
            risk_dist['critical']['percentage']
        )
        assert total_pct == 100
    
    def test_dashboard_empty_database(self, client, app):
        """Test dashboard with empty database."""
        response = client.get('/api/doctor/dashboard')
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['total_patients'] == 0
        assert data['data']['new_cases'] == 0
    
    def test_dashboard_new_cases_count(self, client, sample_predictions):
        """Test that new cases (last 7 days) are counted correctly."""
        response = client.get('/api/doctor/dashboard')
        data = json.loads(response.data)
        
        # All sample predictions were created now, so they should be in new_cases
        assert data['data']['new_cases'] == 4
    
    def test_dashboard_high_risk_count(self, client, sample_predictions):
        """Test that high risk count is correct."""
        response = client.get('/api/doctor/dashboard')
        data = json.loads(response.data)
        
        assert data['data']['high_risk_count'] == 1
    
    def test_dashboard_critical_risk_count(self, client, sample_predictions):
        """Test that critical risk count is correct."""
        response = client.get('/api/doctor/dashboard')
        data = json.loads(response.data)
        
        assert data['data']['critical_risk_count'] == 1


class TestPredictionPersistence:
    """Tests for prediction persistence in the ML predict endpoint."""
    
    def test_prediction_saved_to_database(self, client, app):
        """Test that predictions are saved to the database."""
        payload = {
            'disease': 'diabetes',
            'symptoms': ['increased_thirst', 'frequent_urination', 'fatigue'],
            'age': 45
        }
        
        response = client.post(
            '/api/ml/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        with app.app_context():
            predictions = PredictionHistory.query.all()
            assert len(predictions) == 1
            assert predictions[0].disease == 'diabetes'
            assert predictions[0].patient_age == 45
    
    def test_prediction_risk_level_saved(self, client, app):
        """Test that risk level is correctly saved based on probability."""
        payload = {
            'disease': 'diabetes',
            'symptoms': ['increased_thirst', 'frequent_urination', 'fatigue', 'blurred_vision'],
            'age': 55
        }
        
        response = client.post(
            '/api/ml/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        with app.app_context():
            prediction = PredictionHistory.query.first()
            assert prediction.risk_level in ['low', 'medium', 'high', 'critical']
    
    def test_prediction_symptoms_stored_as_json(self, client, app):
        """Test that symptoms are stored as JSON string."""
        payload = {
            'disease': 'diabetes',
            'symptoms': ['increased_thirst', 'frequent_urination'],
            'age': 40
        }
        
        response = client.post(
            '/api/ml/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        with app.app_context():
            prediction = PredictionHistory.query.first()
            symptoms_list = prediction.get_symptoms_list()
            assert 'increased_thirst' in symptoms_list
            assert 'frequent_urination' in symptoms_list


class TestPredictionHistoryModel:
    """Tests for the PredictionHistory model."""
    
    def test_get_symptoms_list(self, app):
        """Test that symptoms JSON is correctly parsed to list."""
        with app.app_context():
            prediction = PredictionHistory(
                disease='test',
                symptoms=json.dumps(['symptom1', 'symptom2']),
                ml_probability=0.5,
                risk_level='medium'
            )
            
            symptoms = prediction.get_symptoms_list()
            assert symptoms == ['symptom1', 'symptom2']
    
    def test_get_symptoms_list_invalid_json(self, app):
        """Test that invalid JSON returns empty list."""
        with app.app_context():
            prediction = PredictionHistory(
                disease='test',
                symptoms='invalid json',
                ml_probability=0.5,
                risk_level='medium'
            )
            
            symptoms = prediction.get_symptoms_list()
            assert symptoms == []
    
    def test_to_dict(self, app):
        """Test that to_dict returns correct structure."""
        with app.app_context():
            prediction = PredictionHistory(
                disease='diabetes',
                symptoms=json.dumps(['fatigue']),
                ml_probability=0.5,
                bayesian_posterior=0.6,
                risk_level='medium',
                patient_age=40
            )
            db.session.add(prediction)
            db.session.commit()
            
            data = prediction.to_dict()
            assert data['disease'] == 'diabetes'
            assert data['risk_level'] == 'medium'
            assert data['patient_age'] == 40
            assert 'created_at' in data


class TestDoctorDashboardPage:
    """Tests for the Doctor Dashboard page rendering."""
    
    def test_dashboard_page_loads(self, client):
        """Test that doctor dashboard page loads successfully."""
        response = client.get('/doctor-dashboard')
        assert response.status_code == 200
    
    def test_patient_dashboard_requires_login(self, client):
        """Test that patient dashboard redirects unauthenticated users to login."""
        response = client.get('/patient-dashboard')
        # Should redirect to login page
        assert response.status_code == 302
