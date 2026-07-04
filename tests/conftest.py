import io
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_external_services():
    with patch("backend.routes.disease_routes.generate_recommendations") as mock_gemini, \
        patch("backend.routes.disease_routes.generate_tts_audio") as mock_tts, \
        patch("backend.routes.disease_routes.save_history") as mock_history:
        mock_gemini.return_value = {"success": True, "recommendations": "test"}
        mock_tts.return_value = io.BytesIO(b"fake audio")
        mock_history.return_value = None
        yield