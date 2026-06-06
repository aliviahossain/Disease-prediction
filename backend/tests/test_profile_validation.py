import os
import sys
from datetime import date, timedelta

import pytest
from sqlalchemy.exc import OperationalError

from backend import bcrypt, create_app, db
from backend.models.user import User

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRET_KEY", "profile-validation-secret")
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'profile.db'}")

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        user = User(
            username="profileuser",
            email="profile@example.com",
            password_hash=bcrypt.generate_password_hash("password123").decode("utf-8"),
        )
        db.session.add(user)
        db.session.commit()

    with app.test_client() as test_client:
        test_client.post(
            "/login",
            data={"email": "profile@example.com", "password": "password123"},
            follow_redirects=True,
        )
        yield test_client


def test_profile_rejects_invalid_contact_and_future_dob(client):
    future_dob = (date.today() + timedelta(days=1)).isoformat()

    response = client.post(
        "/profile/update",
        data={
            "phone": "not-a-phone",
            "address": "???",
            "emergency_name": "12345",
            "emergency_relation": "@@@",
            "emergency_phone": "phone",
            "dob_day": future_dob.split("-")[2],
            "dob_month": future_dob.split("-")[1],
            "dob_year": future_dob.split("-")[0],
            "gender": "Unknown",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Phone must start with a country code plus sign" in response.data
    assert b"Date of birth cannot be in the future" in response.data

    with client.application.app_context():
        user = User.query.filter_by(email="profile@example.com").first()
        assert user.phone is None
        assert user.dob is None


def test_profile_renders_dob_dropdown_options(client):
    response = client.get("/profile")

    assert response.status_code == 200
    assert b'<option value="">DD</option>' in response.data
    assert b'<option value="">MM</option>' in response.data
    assert b'<option value="">YYYY</option>' in response.data
    assert b'<option value="31"' in response.data


def test_profile_renders_medical_safety_digit_blockers(client):
    response = client.get("/profile")

    assert response.status_code == 200
    assert b'name="allergies"' in response.data
    assert b'name="medical_notes"' in response.data
    assert response.data.count(b'oninput="removeNumbers(this)"') == 2


def test_profile_rejects_unrealistic_old_dob(client):
    response = client.post(
        "/profile/update",
        data={"dob_day": "01", "dob_month": "01", "dob_year": "1000"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Date of birth must be within the last 120 years" in response.data


def test_profile_accepts_valid_contact_demographics_and_metrics(client):
    response = client.post(
        "/profile/update",
        data={
            "phone": "+15551234567",
            "address": "123 Main St",
            "emergency_name": "Jane Doe",
            "emergency_relation": "Sister",
            "emergency_phone": "+15551239999",
            "dob_day": "10",
            "dob_month": "05",
            "dob_year": "1995",
            "gender": "Female",
            "height": "170",
            "weight": "65",
            "allergies": "Peanuts",
            "medical_notes": "Carries medication.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Profile updated successfully" in response.data

    with client.application.app_context():
        user = User.query.filter_by(email="profile@example.com").first()
        assert user.phone == "+15551234567"
        assert user.emergency_phone == "+15551239999"
        assert user.dob.isoformat() == "1995-05-10"
        assert user.bmi == 22.49


def test_profile_rejects_phone_without_country_code_plus(client):
    response = client.post(
        "/profile/update",
        data={
            "phone": "5551234567",
            "emergency_phone": "+15551239999",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Phone must start with a country code plus sign" in response.data


def test_profile_rejects_negative_physical_metrics(client):
    response = client.post(
        "/profile/update",
        data={
            "height": "-170",
            "weight": "-65",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Height must be between 30 and 272" in response.data
    assert b"Weight must be between 1 and 635" in response.data


def test_profile_handles_readonly_database_without_500(client, monkeypatch):
    def raise_readonly_error():
        raise OperationalError(
            "UPDATE user SET emergency_name=? WHERE user.id=?",
            ("Mahesh", 3),
            Exception("attempt to write a readonly database"),
        )

    monkeypatch.setattr(db.session, "commit", raise_readonly_error)

    response = client.post(
        "/profile/update",
        data={
            "emergency_name": "Mahesh",
            "emergency_relation": "Father",
            "emergency_phone": "+919177319640",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"local database is read-only" in response.data


def test_profile_rejects_numbers_in_medical_safety_fields(client):
    response = client.post(
        "/profile/update",
        data={
            "allergies": "Peanuts123",
            "medical_notes": "Needs medicine 2 times daily",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Allergies must contain text only" in response.data
    assert b"Medical notes must contain text only" in response.data


def test_profile_update_preserves_fields_not_in_post(client):
    client.post(
        "/profile/update",
        data={
            "phone": "+15551234567",
            "address": "123 Main St",
            "emergency_name": "Jane Doe",
            "emergency_relation": "Sister",
            "emergency_phone": "+15551239999",
            "dob_day": "10",
            "dob_month": "05",
            "dob_year": "1995",
            "gender": "Female",
            "height": "170",
            "weight": "65",
        },
        follow_redirects=True,
    )

    response = client.post(
        "/profile/update",
        data={"phone": "+15559876543"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Profile updated successfully" in response.data

    with client.application.app_context():
        user = User.query.filter_by(email="profile@example.com").first()
        assert user.phone == "+15559876543"
        assert user.address == "123 Main St"
        assert user.emergency_name == "Jane Doe"
        assert user.dob.isoformat() == "1995-05-10"
        assert user.height == 170.0
        assert user.weight == 65.0


def test_profile_rejects_incomplete_dropdown_dob(client):
    response = client.post(
        "/profile/update",
        data={
            "dob_day": "10",
            "dob_month": "05",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Date of birth requires day, month, and year" in response.data
