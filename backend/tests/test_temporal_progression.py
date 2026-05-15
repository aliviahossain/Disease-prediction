import json
import os
from datetime import datetime, timedelta

import pytest

from backend import create_app, db
from backend.analysis.temporal_progression import analyze_temporal_progression
from backend.models.prediction import PredictionHistory


@pytest.fixture
def app():
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def make_prediction(offset_days, probability, risk_level, symptoms):
    return PredictionHistory(
        disease="diabetes",
        symptoms=json.dumps(symptoms),
        ml_probability=probability,
        bayesian_posterior=probability,
        risk_level=risk_level,
        patient_age=42,
        created_at=datetime.utcnow() + timedelta(days=offset_days),
    )


def test_temporal_progression_detects_worsening_sequence():
    predictions = [
        make_prediction(0, 0.25, "low", ["fatigue"]),
        make_prediction(1, 0.48, "medium", ["fatigue", "increased_thirst"]),
        make_prediction(2, 0.72, "high", ["fatigue", "increased_thirst", "blurred_vision"]),
    ]

    progression = analyze_temporal_progression(predictions, disease="diabetes")

    assert progression["observation_count"] == 3
    assert progression["trend"]["direction"] == "worsening"
    assert progression["trend"]["probability_delta"] == 0.47
    assert progression["recent_weighted_probability"] > 0.48
    assert progression["symptom_progression"]["new_symptoms"] == [
        "blurred_vision",
        "increased_thirst",
    ]
    assert progression["timeline"][1]["risk_transition"] == "escalated"
    assert len(progression["dynamic_updates"]) == 3


def test_temporal_progression_detects_improving_sequence():
    predictions = [
        make_prediction(0, 0.78, "high", ["fatigue", "blurred_vision"]),
        make_prediction(1, 0.52, "medium", ["fatigue"]),
        make_prediction(2, 0.28, "low", ["fatigue"]),
    ]

    progression = analyze_temporal_progression(predictions, disease="diabetes")

    assert progression["trend"]["direction"] == "improving"
    assert progression["timeline"][1]["risk_transition"] == "deescalated"
    assert progression["symptom_progression"]["resolved_symptoms"] == ["blurred_vision"]


def test_temporal_progression_handles_empty_history():
    progression = analyze_temporal_progression([], disease="diabetes")

    assert progression["observation_count"] == 0
    assert progression["trend"]["direction"] == "insufficient_data"
    assert progression["timeline"] == []


def test_temporal_progression_api_returns_anonymous_history(client, app):
    with app.app_context():
        db.session.add(make_prediction(0, 0.22, "low", ["fatigue"]))
        db.session.add(make_prediction(1, 0.64, "high", ["fatigue", "increased_thirst"]))
        db.session.commit()

    response = client.get("/api/ml/temporal-progress?disease=diabetes")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["temporal_progression"]["observation_count"] == 2
    assert data["temporal_progression"]["trend"]["direction"] == "worsening"
