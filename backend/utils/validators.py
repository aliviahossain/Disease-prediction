# backend/utils/validators.py
"""
Centralized input validation for Disease Prediction API routes.
Uses marshmallow for schema enforcement.
"""

import os
import csv
import logging
from functools import wraps

from flask import request, jsonify
from marshmallow import Schema, fields, validate, ValidationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load known disease names from hospital_data.csv at startup
# ---------------------------------------------------------------------------


def _load_known_diseases() -> list[str]:
    """Read disease names from hospital_data.csv. Returns empty list on failure."""
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "hospital_data.csv")
    csv_path = os.path.normpath(csv_path)
    diseases = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Adjust the column name if your CSV uses a different header
                name = row.get("disease") or row.get("Disease") or row.get("name")
                if name and name.strip() not in diseases:
                    diseases.append(name.strip())
    except FileNotFoundError:
        logger.warning(
            "hospital_data.csv not found — disease name validation will be skipped."
        )
    except Exception as exc:
        logger.warning("Could not load disease names for validation: %s", exc)
    return diseases


KNOWN_DISEASES: list[str] = _load_known_diseases()

# Supported AI output languages
SUPPORTED_LANGUAGES: list[str] = ["en", "hi", "gu", "ta"]


# ---------------------------------------------------------------------------
# Marshmallow Schemas
# ---------------------------------------------------------------------------


class BayesInputSchema(Schema):
    """Validates input for the Bayesian calculator endpoint."""

    disease = fields.Str(
        required=True,
        validate=(
            validate.OneOf(KNOWN_DISEASES)
            if KNOWN_DISEASES
            else validate.Length(min=1, max=100)
        ),
        error_messages={"required": "disease is required."},
    )
    prior = fields.Float(
        required=True,
        validate=validate.Range(min=0.0, max=1.0),
        error_messages={
            "required": "prior is required.",
            "validator_failed": "prior must be between 0.0 and 1.0.",
        },
    )
    sensitivity = fields.Float(
        required=True,
        validate=validate.Range(min=0.0, max=1.0),
        error_messages={
            "required": "sensitivity is required.",
            "validator_failed": "sensitivity must be between 0.0 and 1.0.",
        },
    )
    false_positive_rate = fields.Float(
        required=True,
        validate=validate.Range(min=0.0, max=1.0),
        error_messages={
            "required": "false_positive_rate is required.",
            "validator_failed": "false_positive_rate must be between 0.0 and 1.0.",
        },
    )


class SymptomInputSchema(Schema):
    """Validates input for the ML symptom-based prediction endpoint."""

    symptoms = fields.List(
        fields.Str(validate=validate.Length(min=1, max=100)),
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={
            "required": "symptoms list is required.",
            "validator_failed": "Provide between 1 and 50 symptoms.",
        },
    )
    age = fields.Int(
        load_default=None,
        validate=validate.Range(min=0, max=150),
    )
    weight = fields.Float(load_default=None, validate=validate.Range(min=0, max=700))
    height = fields.Float(load_default=None, validate=validate.Range(min=0, max=300))


class AILanguageSchema(Schema):
    """Validates the language parameter for AI recommendation routes."""

    language = fields.Str(
        load_default="en",
        validate=validate.OneOf(
            SUPPORTED_LANGUAGES,
            error="Unsupported language. Choose one of: en, hi, gu, ta.",
        ),
    )


# ---------------------------------------------------------------------------
# Decorator helpers
# ---------------------------------------------------------------------------

_SCHEMA_REGISTRY: dict[str, Schema] = {
    "bayes": BayesInputSchema(),
    "symptoms": SymptomInputSchema(),
    "ai_language": AILanguageSchema(),
}


def validate_input(schema_name: str):
    """
    Decorator that validates the incoming JSON request body against a named schema.
    Returns 400 with a descriptive message on validation failure.

    Usage:
        @app.route("/calculate", methods=["POST"])
        @validate_input("bayes")
        def calculate():
            data = request.validated_data   # pre-validated dict
            ...
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            schema = _SCHEMA_REGISTRY.get(schema_name)
            if schema is None:
                logger.error("Unknown validation schema: '%s'", schema_name)
                return jsonify({"error": "Internal server error: unknown schema."}), 500

            # Accept JSON body; also accept form data gracefully
            if request.is_json:
                raw = request.get_json(silent=True) or {}
            else:
                raw = request.form.to_dict()

            try:
                validated = schema.load(raw)
            except ValidationError as err:
                return (
                    jsonify({"error": "Validation failed.", "details": err.messages}),
                    400,
                )

            # Attach validated data to request for use in the view
            request.validated_data = validated
            return f(*args, **kwargs)

        return wrapper

    return decorator
