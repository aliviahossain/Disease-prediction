# tests/test_validators.py
"""Basic tests for the validators module."""
import pytest
from marshmallow import ValidationError
from backend.utils.validators import BayesInputSchema, AILanguageSchema


class TestBayesInputSchema:
    schema = BayesInputSchema()

    def test_valid_input(self):
        data = {"disease": "Heart Disease", "prior": 0.3,
                "sensitivity": 0.9, "false_positive_rate": 0.1}
        result = self.schema.load(data)
        assert result["prior"] == 0.3

    def test_prior_out_of_range_high(self):
        with pytest.raises(ValidationError) as exc_info:
            self.schema.load({"disease": "Heart Disease", "prior": 2.5,
                              "sensitivity": 0.9, "false_positive_rate": 0.1})
        assert "prior" in exc_info.value.messages

    def test_prior_out_of_range_low(self):
        with pytest.raises(ValidationError) as exc_info:
            self.schema.load({"disease": "Heart Disease", "prior": -0.1,
                              "sensitivity": 0.9, "false_positive_rate": 0.1})
        assert "prior" in exc_info.value.messages

    def test_missing_required_field(self):
        with pytest.raises(ValidationError) as exc_info:
            self.schema.load({"disease": "Heart Disease", "prior": 0.3})
        assert "sensitivity" in exc_info.value.messages


class TestAILanguageSchema:
    schema = AILanguageSchema()

    def test_valid_language(self):
        result = self.schema.load({"language": "hi"})
        assert result["language"] == "hi"

    def test_unsupported_language(self):
        with pytest.raises(ValidationError) as exc_info:
            self.schema.load({"language": "fr"})
        assert "language" in exc_info.value.messages

    def test_defaults_to_english(self):
        result = self.schema.load({})
        assert result["language"] == "en"