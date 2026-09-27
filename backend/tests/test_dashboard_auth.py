from backend.utils.dashboard_auth import (
    is_dashboard_auth_configured,
    is_production_environment,
    verify_dashboard_password,
)


def test_is_dashboard_auth_configured_false_when_unset(monkeypatch):
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)
    assert is_dashboard_auth_configured() is False


def test_is_dashboard_auth_configured_false_for_blank_value(monkeypatch):
    monkeypatch.setenv("DASHBOARD_PASSWORD", "   ")
    assert is_dashboard_auth_configured() is False


def test_is_dashboard_auth_configured_true_when_set(monkeypatch):
    monkeypatch.setenv("DASHBOARD_PASSWORD", "correct-horse-battery-staple")
    assert is_dashboard_auth_configured() is True


def test_is_production_environment_true(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    assert is_production_environment() is True


def test_is_production_environment_false_when_debug_flag_set(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("FLASK_DEBUG", "1")
    assert is_production_environment() is False


def test_is_production_environment_false_in_development(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    assert is_production_environment() is False


def test_verify_dashboard_password_correct_match():
    assert verify_dashboard_password("s3cret", "s3cret") is True


def test_verify_dashboard_password_incorrect_match():
    assert verify_dashboard_password("wrong", "s3cret") is False


def test_verify_dashboard_password_rejects_empty_candidate():
    assert verify_dashboard_password("", "s3cret") is False


def test_verify_dashboard_password_rejects_empty_expected():
    assert verify_dashboard_password("s3cret", "") is False


def test_verify_dashboard_password_rejects_both_empty():
    assert verify_dashboard_password("", "") is False
