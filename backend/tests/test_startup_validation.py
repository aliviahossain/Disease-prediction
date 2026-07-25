"""
Tests for the startup configuration and model file validator.
"""

import os
import sys
from unittest.mock import MagicMock

import pytest

from backend.utils.config_validator import validate_startup_config

# Add parent directory to path to ensure backend imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_production_missing_secret_key(monkeypatch):
    """Test that ValueError is raised in production when SECRET_KEY is missing"""  # noqa: E501
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_123")

    app = MagicMock()

    with pytest.raises(ValueError) as exc_info:
        validate_startup_config(app)

    assert "SECRET_KEY environment variable is required in production" in str(
        exc_info.value
    )


def test_production_weak_secret_key(monkeypatch):
    """Test that ValueError is raised in production when SECRET_KEY is too short/weak"""  # noqa: E501
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    monkeypatch.setenv("SECRET_KEY", "too_short")  # Only 9 chars
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_123")

    app = MagicMock()

    with pytest.raises(ValueError) as exc_info:
        validate_startup_config(app)

    assert "SECRET_KEY is too weak" in str(exc_info.value)


def test_production_missing_gemini_key(monkeypatch):
    """Test that ValueError is raised in production when GEMINI_API_KEY is missing"""  # noqa: E501
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    monkeypatch.setenv("SECRET_KEY", "super_secret_production_key_123456")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    app = MagicMock()

    with pytest.raises(ValueError) as exc_info:
        validate_startup_config(app)

    assert (
        "GEMINI_API_KEY environment variable is required in production"
        in str(exc_info.value)
    )


def test_production_missing_model_files(monkeypatch):
    """Test that FileNotFoundError is raised in production when a model file is missing"""  # noqa: E501
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    monkeypatch.setenv("SECRET_KEY", "super_secret_production_key_123456")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_123")

    # Mock os.path.exists to return False so model files are treated as missing
    monkeypatch.setattr(os.path, "exists", lambda x: False)

    app = MagicMock()

    with pytest.raises(FileNotFoundError) as exc_info:
        validate_startup_config(app)

    assert "Required ML model file" in str(exc_info.value)


def test_development_mode_missing_keys_succeeds(monkeypatch, capsys):
    """Test that in development mode, missing keys/models print warning but do NOT raise errors"""  # noqa: E501
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("FLASK_DEBUG", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Mock os.path.exists to simulate missing models
    monkeypatch.setattr(os.path, "exists", lambda x: False)

    app = MagicMock()

    # Should run successfully without throwing
    validate_startup_config(app)

    # Capture print output and check for warnings
    captured = capsys.readouterr()
    assert "WARNING: GEMINI_API_KEY is not set in development" in captured.out
    assert "WARNING: ML model file" in captured.out


def test_validation_passes_when_valid(monkeypatch):
    """Test that validation passes completely without warning/error when everything is present"""  # noqa: E501
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    monkeypatch.setenv("SECRET_KEY", "super_secret_production_key_123456")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_123")

    # Simulate all models existing
    monkeypatch.setattr(os.path, "exists", lambda x: True)

    app = MagicMock()

    # Should pass without raising any exception
    validate_startup_config(app)
