import re

import pytest

from backend import bcrypt, create_app, db
from backend.models.user import User


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRET_KEY", "csrf-test-secret-key-for-testing")
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test_csrf.db'}")

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = (
        True  # re-enable: create_app() disables when TESTING=True
    )
    app.config["WTF_CSRF_TIME_LIMIT"] = None  # prevent token expiry during test run
    return app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


def _get_csrf_token(client):
    """Load the login page and parse the CSRF token from the rendered HTML."""
    resp = client.get("/login")
    assert resp.status_code == 200, "Login page did not load"
    match = re.search(rb'name="csrf_token"\s+value="([^"]+)"', resp.data)
    assert match, "CSRF token hidden input not found in login page HTML"
    return match.group(1).decode()


# ── Token presence ──────────────────────────────────────────────────────────


def test_csrf_token_present_on_auth_page(client):
    """Auth page must render csrf_token hidden input in both login and signup forms."""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert resp.data.count(b'name="csrf_token"') >= 2


def test_csrf_token_present_on_profile_page(app, client):
    """Profile page must render a csrf_token hidden input."""
    with app.app_context():
        user = User(
            username="profilecsrf",
            email="profilecsrf@example.com",
            password_hash=bcrypt.generate_password_hash("Secure123!").decode("utf-8"),
        )
        db.session.add(user)
        db.session.commit()

    token = _get_csrf_token(client)
    client.post(
        "/login",
        data={
            "email": "profilecsrf@example.com",
            "password": "Secure123!",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    resp = client.get("/profile")
    assert resp.status_code == 200
    assert b'name="csrf_token"' in resp.data


# ── Rejection without token ─────────────────────────────────────────────────


def test_login_without_csrf_returns_400(client):
    """POST /login with no CSRF token must be rejected."""
    resp = client.post(
        "/login",
        data={"email": "anyone@example.com", "password": "password123"},
    )
    assert resp.status_code == 400


def test_signup_without_csrf_returns_400(client):
    """POST /signup with no CSRF token must be rejected."""
    resp = client.post(
        "/signup",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 400


def test_profile_update_without_csrf_returns_400(app, client):
    """POST /profile/update with no CSRF token must be rejected."""
    with app.app_context():
        user = User(
            username="csrfuser",
            email="csrf@example.com",
            password_hash=bcrypt.generate_password_hash("Secure123!").decode("utf-8"),
        )
        db.session.add(user)
        db.session.commit()

    token = _get_csrf_token(client)
    client.post(
        "/login",
        data={
            "email": "csrf@example.com",
            "password": "Secure123!",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    resp = client.post("/profile/update", data={"phone": "+15551234567"})
    assert resp.status_code == 400


# ── Acceptance with valid token ─────────────────────────────────────────────


def test_login_with_valid_csrf_is_not_rejected_for_csrf(client):
    """POST /login with a valid CSRF token must not return 400 (CSRF passes, auth may still fail)."""
    token = _get_csrf_token(client)
    resp = client.post(
        "/login",
        data={
            "email": "wrong@example.com",
            "password": "wrongpassword",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert resp.status_code != 400


def test_signup_with_valid_csrf_is_not_rejected_for_csrf(client):
    """POST /signup with a valid CSRF token must not return 400 (CSRF passes)."""
    token = _get_csrf_token(client)
    resp = client.post(
        "/signup",
        data={
            "username": "newuser",
            "email": "new@example.com",
            "password": "Secure123!",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert resp.status_code != 400
