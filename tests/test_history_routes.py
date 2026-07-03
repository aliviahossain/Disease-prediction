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


# ── POST /api/history ─────────────────────────────────────────────────────────

def test_add_history_unauthenticated(client):
    res = client.post("/api/history", json={
        "prediction_type": "bayes",
        "disease": "flu",
        "probability": 0.7
    })
    assert res.status_code in (401, 403)


def test_add_history_invalid_prediction_type_unauthenticated(client):
    res = client.post("/api/history", json={
        "prediction_type": "unknown_type",
        "disease": "flu",
        "probability": 0.7
    })
    assert res.status_code in (400, 401, 403)


# ── GET /api/history ──────────────────────────────────────────────────────────

def test_list_history_unauthenticated(client):
    res = client.get("/api/history")
    assert res.status_code in (401, 403)


# ── DELETE /api/history ───────────────────────────────────────────────────────

def test_clear_history_unauthenticated(client):
    res = client.delete("/api/history")
    assert res.status_code in (401, 403)


# ── GET /api/history/<id> ─────────────────────────────────────────────────────

def test_get_history_entry_unauthenticated(client):
    res = client.get("/api/history/1")
    assert res.status_code in (401, 403, 404)


# ── DELETE /api/history/<id> ──────────────────────────────────────────────────

def test_delete_history_entry_unauthenticated(client):
    res = client.delete("/api/history/1")
    assert res.status_code in (401, 403, 404)