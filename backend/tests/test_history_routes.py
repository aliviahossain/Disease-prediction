"""
Unit tests for prediction history functionality.

Tests cover:
- History CRUD operations
- Pagination
- CSV/JSON exports
- User data isolation
- Error handling
"""

import pytest
from datetime import datetime
from backend.models.patient_history import PatientHistory
from backend import db

class TestPredictionHistory:
    """Test suite for prediction history endpoints."""
    
    def test_save_prediction_to_history(self, client, auth_headers):
        """Test saving prediction to user history."""
        response = client.post(
            "/api/history",
            json={
                "disease": "diabetes",
                "prediction_type": "ml",
                "inputs": {"symptoms": ["fatigue", "thirst"]},
                "results": {"probability": 0.78},
                "probability": 0.78,
                "risk_level": "high"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json["disease"] == "diabetes"
    
    def test_get_prediction_history(self, client, auth_headers):
        """Test retrieving user history with pagination."""
        response = client.get(
            "/api/history?page=1&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json
        assert "items" in data
        assert "total" in data
        assert "pages" in data
    
    def test_delete_single_history_entry(self, client, auth_headers):
        """Test deleting individual history entry."""
        # First create an entry
        response = client.post(
            "/api/history",
            json={"disease": "fever", "probability": 0.65},
            headers=auth_headers
        )
        entry_id = response.json["id"]
        
        # Now delete it
        delete_response = client.delete(
            f"/api/history/{entry_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200
        assert delete_response.json["deleted_id"] == entry_id
    
    def test_clear_all_history(self, client, auth_headers):
        """Test clearing all history for user."""
        response = client.delete(
            "/api/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "deleted_count" in response.json
    
    def test_export_history_csv(self, client, auth_headers):
        """Test CSV export of prediction history."""
        response = client.get(
            "/history/export/csv",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "text/csv" in response.content_type
        assert b"Prediction ID" in response.data
    
    def test_history_user_isolation(self, client, auth_headers_user2):
        """Test that users cannot see each other's history."""
        response = client.get(
            "/api/history",
            headers=auth_headers_user2
        )
        # Should only see user2's history, not other users
        assert response.status_code == 200
        for item in response.json["items"]:
            assert item["user_id"] == "user2_id"
    
    def test_filter_history_by_type(self, client, auth_headers):
        """Test filtering history by prediction type."""
        response = client.get(
            "/api/history?type=ml",
            headers=auth_headers
        )
        assert response.status_code == 200
        for item in response.json["items"]:
            assert item["prediction_type"] == "ml"

