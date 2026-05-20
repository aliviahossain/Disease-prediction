"""
Tests for issue #230 — patient history end-to-end.

Covers:
  - PatientHistory model can be created and serialised
  - save_history() persists for authenticated users, no-ops anonymously,
    and never raises on bad input
  - /api/history returns only the calling user's rows
  - DELETE /api/history/<id> only allows owners to delete
  - Pagination metadata is correct

These tests assume:
  - `pytest` and `flask_login` are installed
  - The app factory in backend/__init__.py is `create_app`
  - A test User model exists with .id, .email/.username, .password
  - The login route accepts JSON {email, password} (adjust login_as
    if your auth route differs)

If any of those don't match, edit the fixtures below — the test
logic itself is the part worth preserving.
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from backend import create_app, db
from backend.models.patient_history import PatientHistory
from backend.services.history_service import save_history, _classify_risk


# --------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------- #
@pytest.fixture
def app():
    """A Flask app bound to an isolated, in-memory SQLite DB."""
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.environ["SECRET_KEY"] = "test-secret-key-not-for-prod"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    """Factory: create a user, return its id."""
    from backend.models.user import User  # adjust to your import path
    from backend import bcrypt

    counter = {"n": 0}

    def _make(email=None, password="hunter22"):
        counter["n"] += 1
        email = email or f"user{counter['n']}@example.com"
        u = User(
            email=email,
            password=bcrypt.generate_password_hash(password).decode("utf-8"),
        )
        db.session.add(u)
        db.session.commit()
        return u.id, email, password

    return _make


def login_as(client, email, password):
    """Send credentials to the existing login endpoint and return the
    response. Adjust if your login URL or fields differ."""
    return client.post(
        "/login",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
        follow_redirects=True,
    )


# --------------------------------------------------------------------- #
# Unit tests: model + service
# --------------------------------------------------------------------- #
class TestPatientHistoryModel:
    def test_to_dict_round_trip(self, app, make_user):
        with app.app_context():
            user_id, _, _ = make_user()
            entry = PatientHistory(
                user_id=user_id,
                prediction_type="bayes",
                disease="Diabetes",
                inputs_json=json.dumps({"prior": 0.1}),
                results_json=json.dumps({"posterior": 0.42}),
                probability=0.42,
                risk_level="medium",
            )
            db.session.add(entry)
            db.session.commit()

            d = entry.to_dict()
            assert d["disease"] == "Diabetes"
            assert d["probability"] == pytest.approx(0.42)
            assert d["probability_percent"] == pytest.approx(42.0)
            assert d["inputs"] == {"prior": 0.1}
            assert d["results"] == {"posterior": 0.42}
            assert d["risk_level"] == "medium"

    def test_to_dict_handles_bad_json(self, app, make_user):
        with app.app_context():
            user_id, _, _ = make_user()
            entry = PatientHistory(
                user_id=user_id,
                prediction_type="bayes",
                inputs_json="this is not json",
                results_json=None,
            )
            db.session.add(entry)
            db.session.commit()

            d = entry.to_dict()
            assert d["inputs"] is None
            assert d["results"] is None


class TestSaveHistoryService:
    def test_save_persists_row(self, app, make_user):
        with app.app_context():
            user_id, _, _ = make_user()
            entry = save_history(
                user_id=user_id,
                prediction_type="bayes",
                disease="Hypertension",
                inputs={"prior": 0.2, "sensitivity": 0.9},
                results={"posterior": 0.55},
                probability=0.55,
            )
            assert entry is not None
            assert entry.id is not None
            assert entry.risk_level == "medium"
            assert PatientHistory.query.count() == 1

    def test_save_for_anonymous_user_is_noop(self, app):
        with app.app_context():
            entry = save_history(
                user_id=None,
                prediction_type="bayes",
                probability=0.5,
            )
            assert entry is None
            assert PatientHistory.query.count() == 0

    def test_save_never_raises_on_bad_input(self, app, make_user):
        """The function should swallow errors and return None — a failure
        to record history must never break the prediction itself."""
        with app.app_context():
            user_id, _, _ = make_user()
            # `inputs` is not serialisable but should be tolerated.
            class Weird:  # not JSON-friendly
                pass

            entry = save_history(
                user_id=user_id,
                prediction_type="bayes",
                inputs={"weird": Weird()},
                probability="not-a-number",  # also bad
            )
            # Probability conversion fails → entry should still be None
            # (or saved with probability=None). Either way, no exception.
            # We don't assert specific behavior here, just that nothing blew up.
            assert PatientHistory.query.count() in (0, 1)

    @pytest.mark.parametrize("prob,expected", [
        (0.0,  "low"),
        (0.29, "low"),
        (0.30, "medium"),
        (0.69, "medium"),
        (0.70, "high"),
        (1.0,  "high"),
        (None, None),
    ])
    def test_risk_classifier(self, prob, expected):
        assert _classify_risk(prob) == expected


# --------------------------------------------------------------------- #
# Integration tests: HTTP API
# --------------------------------------------------------------------- #
class TestHistoryAPI:
    def test_list_requires_auth(self, client):
        resp = client.get("/api/history")
        assert resp.status_code == 401
        body = resp.get_json()
        assert body and body.get("error") == "authentication_required"

    def test_list_returns_only_own_entries(self, app, client, make_user):
        # Set up two users with entries each.
        with app.app_context():
            user1_id, email1, pw1 = make_user()
            user2_id, _,     _   = make_user()
            save_history(user_id=user1_id, prediction_type="bayes",
                         disease="A", probability=0.4)
            save_history(user_id=user1_id, prediction_type="bayes",
                         disease="B", probability=0.6)
            save_history(user_id=user2_id, prediction_type="bayes",
                         disease="C", probability=0.8)

        login_as(client, email1, pw1)
        resp = client.get("/api/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 2
        diseases = {item["disease"] for item in data["items"]}
        assert diseases == {"A", "B"}  # never C

    def test_pagination(self, app, client, make_user):
        with app.app_context():
            user_id, email, pw = make_user()
            for i in range(25):
                save_history(
                    user_id=user_id,
                    prediction_type="bayes",
                    disease=f"D{i}",
                    probability=i / 25.0,
                )

        login_as(client, email, pw)
        resp = client.get("/api/history?per_page=10&page=2")
        data = resp.get_json()
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert data["total"] == 25
        assert data["pages"] == 3
        assert len(data["items"]) == 10
        assert data["has_prev"] is True
        assert data["has_next"] is True

    def test_delete_only_allows_owner(self, app, client, make_user):
        with app.app_context():
            owner_id, owner_email, owner_pw = make_user()
            other_id, other_email, other_pw = make_user()
            owned = save_history(user_id=owner_id, prediction_type="bayes",
                                 disease="Owned", probability=0.5)
            owned_id = owned.id

        # Other user tries to delete — must get 404 (not 403, to avoid
        # leaking existence).
        login_as(client, other_email, other_pw)
        resp = client.delete(f"/api/history/{owned_id}")
        assert resp.status_code == 404

        # Verify it's still there.
        with app.app_context():
            assert PatientHistory.query.get(owned_id) is not None

        # Owner can delete.
        client.get("/logout", follow_redirects=True)
        login_as(client, owner_email, owner_pw)
        resp = client.delete(f"/api/history/{owned_id}")
        assert resp.status_code == 200

        with app.app_context():
            assert PatientHistory.query.get(owned_id) is None

    def test_clear_all_only_affects_caller(self, app, client, make_user):
        with app.app_context():
            user1_id, email1, pw1 = make_user()
            user2_id, _,      _   = make_user()
            save_history(user_id=user1_id, prediction_type="bayes",
                         disease="X", probability=0.1)
            save_history(user_id=user1_id, prediction_type="bayes",
                         disease="Y", probability=0.2)
            save_history(user_id=user2_id, prediction_type="bayes",
                         disease="Z", probability=0.3)

        login_as(client, email1, pw1)
        resp = client.delete("/api/history")
        assert resp.status_code == 200
        assert resp.get_json()["deleted_count"] == 2

        with app.app_context():
            remaining = PatientHistory.query.all()
            assert len(remaining) == 1
            assert remaining[0].user_id == user2_id

    def test_filter_by_type(self, app, client, make_user):
        with app.app_context():
            user_id, email, pw = make_user()
            save_history(user_id=user_id, prediction_type="bayes",
                         disease="A", probability=0.2)
            save_history(user_id=user_id, prediction_type="eye",
                         disease="Cataract", probability=0.9)

        login_as(client, email, pw)
        resp = client.get("/api/history?type=eye")
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["disease"] == "Cataract"