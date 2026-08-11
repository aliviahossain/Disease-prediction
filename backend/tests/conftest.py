import io
import pytest
from unittest.mock import patch
from dotenv import load_dotenv
from run import app as flask_app

# Load environment variables
load_dotenv()


# The crucial fixture for pytest-flask
@pytest.fixture
def app():
    """Yields the Flask application instance for pytest-flask."""
    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})

    with flask_app.app_context():
        yield flask_app


@pytest.fixture(autouse=True)
def clear_test_isolation_state():
    """Clears failed login attempts and rate limiter states to ensure test isolation."""
    try:
        from backend.routes.auth_routes import LOGIN_ATTEMPTS

        LOGIN_ATTEMPTS.clear()
    except Exception:
        pass

    try:
        from backend.middleware.security import rate_limiter

        if hasattr(rate_limiter, "backend"):
            backend = rate_limiter.backend
            if hasattr(backend, "_requests"):
                backend._requests.clear()
            elif hasattr(backend, "db_path"):
                import sqlite3

                conn = sqlite3.connect(backend.db_path)
                conn.execute("DELETE FROM rate_limits")
                conn.commit()
                conn.close()
    except Exception:
        pass


# Your mocks to prevent real API calls during testing
@pytest.fixture(autouse=True)
def mock_external_services():
    with patch(
        "backend.routes.disease_routes.generate_recommendations"
    ) as mock_gemini, patch(
        "backend.routes.disease_routes.generate_tts_audio"
    ) as mock_tts, patch(
        "backend.routes.disease_routes.save_history"
    ) as mock_history:
        mock_gemini.return_value = {"success": True, "recommendations": "test"}
        mock_tts.return_value = io.BytesIO(b"fake audio")
        mock_history.return_value = None
        yield
