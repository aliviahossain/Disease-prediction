import pytest
from backend import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


# ── /text-to-speech ───────────────────────────────────────────────────────────

def test_tts_invalid_language(client):
    res = client.post("/text-to-speech", json={
        "text": "hello",
        "language": "french"
    })
    assert res.status_code == 400


def test_tts_valid_language(client):
    res = client.post("/text-to-speech", json={
        "text": "hello",
        "language": "english"
    })
    assert res.status_code == 200


def test_tts_exceeds_max_length(client):
    res = client.post("/text-to-speech", json={
        "text": "a" * 2001,
        "language": "english"
    })
    assert res.status_code == 400


def test_tts_exactly_max_length(client):
    res = client.post("/text-to-speech", json={
        "text": "a" * 2000,
        "language": "english"
    })
    assert res.status_code == 200


def test_tts_no_text(client):
    res = client.post("/text-to-speech", json={
        "language": "english"
    })
    assert res.status_code == 400


# ── /gemini-recommendations ───────────────────────────────────────────────────

def test_gemini_invalid_language(client):
    res = client.post("/gemini-recommendations", json={
        "disease_name": "flu",
        "prior_probability": 0.3,
        "posterior_probability": 0.7,
        "test_result": "positive",
        "language": "french"
    })
    assert res.status_code == 400


def test_gemini_invalid_test_result(client):
    res = client.post("/gemini-recommendations", json={
        "disease_name": "flu",
        "prior_probability": 0.3,
        "posterior_probability": 0.7,
        "test_result": "maybe",
        "language": "english"
    })
    print(res.data)
    assert res.status_code == 400


def test_gemini_valid_inputs_accepted(client):
    res = client.post("/gemini-recommendations", json={
        "disease_name": "flu",
        "prior_probability": 0.3,
        "posterior_probability": 0.7,
        "test_result": "positive",
        "language": "hindi"
    })
    assert res.status_code == 200


# ── /disease ──────────────────────────────────────────────────────────────────

def test_disease_valid_input(client):
    res = client.post("/disease", json={
        "pD": 0.1,
        "sensitivity": 0.9,
        "falsePositive": 0.05,
        "testResult": "positive"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "p_d_given_result" in data


def test_disease_invalid_prevalence(client):
    res = client.post("/disease", json={
        "pD": 1.5,
        "sensitivity": 0.9,
        "falsePositive": 0.05,
        "testResult": "positive"
    })
    assert res.status_code == 400


def test_disease_invalid_test_result(client):
    res = client.post("/disease", json={
        "pD": 0.1,
        "sensitivity": 0.9,
        "falsePositive": 0.05,
        "testResult": "maybe"
    })
    assert res.status_code == 400


# ── _sanitize_name ────────────────────────────────────────────────────────────

def test_sanitize_via_preset_strips_script_tag(client):
    res = client.post("/preset", json={
        "disease": "<script>alert(1)</script>"
    })
    assert res.status_code == 404


def test_sanitize_via_preset_truncates_long_name(client):
    res = client.post("/preset", json={
        "disease": "a" * 200
    })
    assert res.status_code == 404