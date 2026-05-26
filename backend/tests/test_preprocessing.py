import pytest

from backend.preprocessing import (PreprocessingError,
                                   clean_prediction_payload, normalize_key)

VALID_SYMPTOMS = {
    "increased_thirst",
    "frequent_urination",
    "fatigue",
    "blurred_vision",
}


def test_normalize_key_handles_display_labels():
    assert normalize_key(" Increased Thirst ") == "increased_thirst"
    assert normalize_key("Frequent-Urination") == "frequent_urination"
    assert normalize_key("Blurred <Vision>!") == "blurred_vision"


def test_clean_prediction_payload_normalizes_and_deduplicates_symptoms():
    cleaned = clean_prediction_payload(
        {
            "disease": "Diabetes Type 2",
            "symptoms": [
                "Increased Thirst",
                "increased_thirst",
                "Frequent Urination",
                "unknown symptom",
            ],
            "age": "45",
            "height_cm": "172.5",
            "weight_kg": "80",
        },
        valid_symptoms=VALID_SYMPTOMS,
    )

    assert cleaned.disease == "diabetes_type_2"
    assert cleaned.symptoms == ["increased_thirst", "frequent_urination"]
    assert cleaned.age == 45
    assert cleaned.height_cm == 172.5
    assert cleaned.weight_kg == 80.0
    assert cleaned.dropped_symptoms == ["unknown_symptom"]


def test_clean_prediction_payload_accepts_comma_separated_symptoms():
    cleaned = clean_prediction_payload(
        {
            "symptoms": "fatigue, blurred vision",
            "age": "",
            "height_cm": None,
            "weight_kg": None,
        },
        valid_symptoms=VALID_SYMPTOMS,
        require_disease=False,
    )

    assert cleaned.disease is None
    assert cleaned.symptoms == ["fatigue", "blurred_vision"]
    assert cleaned.age is None


@pytest.mark.parametrize(
    "payload,error",
    [
        ({"disease": "", "symptoms": ["fatigue"]}, "Disease not specified"),
        ({"disease": "diabetes", "symptoms": []}, "No valid symptoms provided"),
        ({"disease": "diabetes", "symptoms": ["fatigue"], "age": 140}, "Age"),
        ({"disease": "diabetes", "symptoms": ["fatigue"], "height_cm": 10}, "Height"),
        ({"disease": "diabetes", "symptoms": ["fatigue"], "weight_kg": 0}, "Weight"),
    ],
)
def test_clean_prediction_payload_rejects_invalid_values(payload, error):
    with pytest.raises(PreprocessingError, match=error):
        clean_prediction_payload(payload, valid_symptoms=VALID_SYMPTOMS)
