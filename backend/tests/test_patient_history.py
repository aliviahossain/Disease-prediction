"""
Tests for issue #230 — patient history.

This file is split into two tiers:

  1. Tier-1 tests use only the model and service layers — no User rows,
     no HTTP. They should pass on any setup.

  2. Tier-2 tests (TestHistoryAPI, the @make_user fixture) need to create
     real User rows so flask_login has someone to log in. They are
     marked with @pytest.mark.skip pending confirmation of the User
     model's column names. Remove the skip decorator once the
     `make_user` fixture below is updated to match your User model
     (the only thing it needs to figure out is which kwargs the User
     constructor accepts and which fields are NOT NULL).

The fixture also fixes the Windows-only `PermissionError` on teardown
by disposing the SQLAlchemy engine and retrying the unlink.
"""

import json
import os
import tempfile
import time

import pytest

from backend import create_app, db
from backend.models.patient_history import PatientHistory
from backend.services.history_service import _classify_risk, save_history


# --------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------- #
@pytest.fixture
def app():
    """Flask app bound to an isolated SQLite DB.

    Windows-safe teardown:
      - close the mkstemp file handle immediately (otherwise it holds a
        lock on the file even before SQLAlchemy opens it)
      - dispose the engine before unlinking so pooled connections release
        their handles
      - retry unlink with a short sleep, since Windows sometimes takes a
        moment to actually release the handle.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(db_fd)  # release mkstemp's own handle

    os.environ["SECRET_KEY"] = "test-secret-key-not-for-prod"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()  # critical on Windows

    # Retry unlink — on Windows the file may be briefly locked
    # even after engine.dispose().
    for attempt in range(10):
        try:
            os.unlink(db_path)
            break
        except PermissionError:
            time.sleep(0.1)
    else:
        # Give up quietly; the temp file will be cleaned up by the OS.
        pass


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    """Create a User row and return (user_id, email, password).

    ⚠️  This fixture's body needs to match your actual User model.
    The repo's `User` doesn't accept `password=` as a kwarg — likely
    it uses `password_hash` or a setter property. Update the User(...)
    call below once you've confirmed the field names from
    backend/models/user.py.
    """
    from backend import bcrypt
    from backend.models.user import User

    counter = {"n": 0}

    def _make(email=None, password="hunter22"):
        counter["n"] += 1
        email = email or f"user{counter['n']}@example.com"
        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        # Setup kwargs to match User model columns
        u = User(username=email.split("@")[0], email=email, password_hash=pw_hash)

        db.session.add(u)
        db.session.commit()
        return u.id, email, password

    return _make


def login_session(client, user_id):
    """Mark the flask_login session as authenticated for `user_id`.

    Bypasses the /login route so this fixture doesn't depend on whatever
    URL / payload shape your auth blueprint expects.
    """
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True


# --------------------------------------------------------------------- #
# Tier 1: model + service tests (no users, no HTTP)
# --------------------------------------------------------------------- #
class TestPatientHistoryModelStandalone:
    """These tests insert PatientHistory rows with a synthetic user_id
    that isn't tied to a real User row. They exercise the model's
    serialization and the service's no-op / risk-classification behavior.

    NOTE: requires the foreign-key constraint on PatientHistory.user_id
    to NOT be enforced at the DB level. SQLite doesn't enforce FKs by
    default, so this works out of the box.
    """

    def test_to_dict_round_trip(self, app):
        with app.app_context():
            entry = PatientHistory(
                user_id=999,
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

    def test_to_dict_handles_bad_json(self, app):
        with app.app_context():
            entry = PatientHistory(
                user_id=999,
                prediction_type="bayes",
                inputs_json="this is not json",
                results_json=None,
            )
            db.session.add(entry)
            db.session.commit()

            d = entry.to_dict()
            assert d["inputs"] is None
            assert d["results"] is None


class TestSaveHistoryServiceStandalone:
    def test_save_persists_row(self, app):
        with app.app_context():
            entry = save_history(
                user_id=999,
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

    def test_save_never_raises_on_bad_input(self, app):
        """A history failure must never break the prediction itself."""
        with app.app_context():

            class Weird:  # not JSON-friendly
                pass

            save_history(
                user_id=999,
                prediction_type="bayes",
                inputs={"weird": Weird()},
                probability="not-a-number",
            )
            # Either it saved with probability=None, or it noped out.
            # Either way, no exception bubbled up.
            assert PatientHistory.query.count() in (0, 1)

    @pytest.mark.parametrize(
        "prob,expected",
        [
            (0.0, "low"),
            (0.29, "low"),
            (0.30, "medium"),
            (0.69, "medium"),
            (0.70, "high"),
            (1.0, "high"),
            (None, None),
        ],
    )
    def test_risk_classifier(self, prob, expected):
        assert _classify_risk(prob) == expected


class TestHistoryAPIStandalone:
    def test_list_requires_auth(self, client):
        resp = client.get("/api/history")
        assert resp.status_code == 401
        body = resp.get_json()
        assert body and body.get("error") == "authentication_required"


# --------------------------------------------------------------------- #
# Tier 2: full integration — gated until the User model is wired up
# --------------------------------------------------------------------- #
class TestHistoryAPI:
    def test_list_returns_only_own_entries(self, app, client, make_user):
        with app.app_context():
            user1_id, _, _ = make_user()
            user2_id, _, _ = make_user()
            save_history(
                user_id=user1_id, prediction_type="bayes", disease="A", probability=0.4
            )
            save_history(
                user_id=user1_id, prediction_type="bayes", disease="B", probability=0.6
            )
            save_history(
                user_id=user2_id, prediction_type="bayes", disease="C", probability=0.8
            )

        login_session(client, user1_id)
        resp = client.get("/api/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 2
        diseases = {item["disease"] for item in data["items"]}
        assert diseases == {"A", "B"}

    def test_pagination(self, app, client, make_user):
        with app.app_context():
            user_id, _, _ = make_user()
            for i in range(25):
                save_history(
                    user_id=user_id,
                    prediction_type="bayes",
                    disease=f"D{i}",
                    probability=i / 25.0,
                )

        login_session(client, user_id)
        resp = client.get("/api/history?per_page=10&page=2")
        data = resp.get_json()
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert data["total"] == 25
        assert data["pages"] == 3
        assert len(data["items"]) == 10

    def test_delete_another_user_entry_fails(self, app, client, make_user):
        with app.app_context():
            owner_id, _, _ = make_user()
            other_id, _, _ = make_user()
            owned = save_history(
                user_id=owner_id,
                prediction_type="bayes",
                disease="Owned",
                probability=0.5,
            )
            owned_id = owned.id

        login_session(client, other_id)
        resp = client.delete(f"/api/history/{owned_id}")
        assert resp.status_code == 404
        with app.app_context():
            assert PatientHistory.query.get(owned_id) is not None

    def test_delete_own_entry_succeeds(self, app, client, make_user):
        with app.app_context():
            owner_id, _, _ = make_user()
            owned = save_history(
                user_id=owner_id,
                prediction_type="bayes",
                disease="Owned",
                probability=0.5,
            )
            owned_id = owned.id

        login_session(client, owner_id)
        resp = client.delete(f"/api/history/{owned_id}")
        assert resp.status_code == 200
        with app.app_context():
            assert PatientHistory.query.get(owned_id) is None

    def test_clear_all_only_affects_caller(self, app, client, make_user):
        with app.app_context():
            user1_id, _, _ = make_user()
            user2_id, _, _ = make_user()
            save_history(
                user_id=user1_id, prediction_type="bayes", disease="X", probability=0.1
            )
            save_history(
                user_id=user1_id, prediction_type="bayes", disease="Y", probability=0.2
            )
            save_history(
                user_id=user2_id, prediction_type="bayes", disease="Z", probability=0.3
            )

        login_session(client, user1_id)
        resp = client.delete("/api/history")
        assert resp.status_code == 200
        assert resp.get_json()["deleted_count"] == 2

        with app.app_context():
            remaining = PatientHistory.query.all()
            assert len(remaining) == 1
            assert remaining[0].user_id == user2_id

    def test_filter_by_type(self, app, client, make_user):
        with app.app_context():
            user_id, _, _ = make_user()
            save_history(
                user_id=user_id, prediction_type="bayes", disease="A", probability=0.2
            )
            save_history(
                user_id=user_id,
                prediction_type="eyes",
                disease="Cataract",
                probability=0.9,
            )

        login_session(client, user_id)
        resp = client.get("/api/history?type=eyes")
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["disease"] == "Cataract"
