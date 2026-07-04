import io
import pytest
from unittest.mock import patch, MagicMock
from run import app as flask_app

# The crucial fixture that fixes your CI pipeline error!
@pytest.fixture
def app():
    """Yields the Flask application instance for pytest-flask."""
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False 
    })
    
    with flask_app.app_context():
        yield flask_app

# Your existing mock fixture
@pytest.fixture(autouse=True)
def mock_external_services():
    with patch("backend.routes.disease_routes.generate_recommendations") as mock_gemini, \
         patch("backend.routes.disease_routes.generate_tts_audio") as mock_tts, \
         patch("backend.routes.disease_routes.save_history") as mock_history:
        mock_gemini.return_value = {"success": True, "recommendations": "test"}
        mock_tts.return_value = io.BytesIO(b"fake audio")
        mock_history.return_value = None
        yield