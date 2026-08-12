# tests/test_ai_language.py
"""Smoke tests for AI language validation (uses mocked Gemini API)."""
import pytest
from unittest.mock import patch, MagicMock
from marshmallow import ValidationError
from backend.utils.validators import AILanguageSchema


class TestAILanguageValidation:
    schema = AILanguageSchema()

    @pytest.mark.parametrize("lang", ["en", "hi", "gu", "ta"])
    def test_all_supported_languages_accepted(self, lang):
        result = self.schema.load({"language": lang})
        assert result["language"] == lang

    @pytest.mark.parametrize("bad_lang", ["fr", "de", "zh", "es", "EN", "Hindi", ""])
    def test_unsupported_language_rejected(self, bad_lang):
        with pytest.raises(ValidationError):
            self.schema.load({"language": bad_lang})

    def test_missing_language_defaults_to_english(self):
        result = self.schema.load({})
        assert result["language"] == "en"