"""
Regression coverage for issue #596: a malformed or unexpected Gemini API
response must never escape as an unhandled exception (and therefore a raw
500 with a stack trace) from either generate_recommendations or
generate_chat_response.
"""

from unittest.mock import MagicMock, patch

from backend.utils import gemini_helper


def _mock_configure_gemini_with_client(mock_client):
    """Patch configure_gemini so it assigns our mock client without needing a real API key."""

    def _fake_configure():
        gemini_helper.client = mock_client

    return patch.object(gemini_helper, "configure_gemini", side_effect=_fake_configure)


class _RaisingTextResponse:
    """Simulates a genai response object whose .text raises when accessed,
    e.g. because the content was safety-filtered and only a finish_reason
    is available."""

    @property
    def text(self):
        raise ValueError("Response has no text; finish_reason=SAFETY")


def test_generate_recommendations_survives_text_access_raising():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = (
        lambda **kwargs: _RaisingTextResponse()
    )

    with _mock_configure_gemini_with_client(mock_client):
        result = gemini_helper.generate_recommendations(
            disease_name="flu",
            prior_probability=0.2,
            posterior_probability=0.6,
        )

    assert result["success"] is False
    assert "recommendations" in result


def test_generate_recommendations_survives_all_models_raising():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError(
        "upstream unavailable"
    )

    with _mock_configure_gemini_with_client(mock_client):
        result = gemini_helper.generate_recommendations(
            disease_name="flu",
            prior_probability=0.2,
            posterior_probability=0.6,
        )

    assert result["success"] is False
    assert "error" in result


def test_generate_recommendations_accepts_non_json_plain_text():
    # Gemini occasionally returns a plain-text explanation instead of the
    # requested structured format. This must be accepted as-is, not parsed
    # as JSON.
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "I'm not entirely sure, please consult a doctor."
    mock_client.models.generate_content.return_value = mock_response

    with _mock_configure_gemini_with_client(mock_client):
        result = gemini_helper.generate_recommendations(
            disease_name="flu",
            prior_probability=0.2,
            posterior_probability=0.6,
        )

    assert result["success"] is True
    assert (
        result["recommendations"] == "I'm not entirely sure, please consult a doctor."
    )


def test_generate_recommendations_missing_api_key_is_handled():
    with patch.object(
        gemini_helper,
        "configure_gemini",
        side_effect=ValueError("GEMINI_API_KEY environment variable is not set"),
    ):
        result = gemini_helper.generate_recommendations(
            disease_name="flu",
            prior_probability=0.2,
            posterior_probability=0.6,
        )

    assert result["success"] is False
    assert "API key" in result["recommendations"]


def test_generate_chat_response_survives_text_access_raising():
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = lambda *a, **k: _RaisingTextResponse()
    mock_client.chats.create.return_value = mock_chat

    with _mock_configure_gemini_with_client(mock_client):
        result = gemini_helper.generate_chat_response([{"role": "user", "text": "hi"}])

    assert result["success"] is False
    assert "response" in result


def test_generate_chat_response_survives_send_message_raising():
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = RuntimeError("upstream unavailable")
    mock_client.chats.create.return_value = mock_chat

    with _mock_configure_gemini_with_client(mock_client):
        result = gemini_helper.generate_chat_response([{"role": "user", "text": "hi"}])

    assert result["success"] is False
    assert "error" in result
