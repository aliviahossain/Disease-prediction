from backend.models.ml_model import ml_model


def test_ml_prediction_returns_feature_impacts_and_summary():
    result = ml_model.predict_disease_probability(
        "diabetes",
        ["increased_thirst", "fatigue"],
        age=30,
        height_cm=170,
        weight_kg=70,
    )

    assert "feature_impacts" in result
    assert isinstance(result["feature_impacts"], list)
    assert result[
        "feature_impacts"
    ], "Expected at least one feature impact entry."
    assert any(
        item["direction"] == "positive" for item in result["feature_impacts"]
    )
    assert any(
        item["direction"] == "negative" for item in result["feature_impacts"]
    )

    assert "explanation_summary" in result
    assert isinstance(result["explanation_summary"], str)
    assert result["explanation_summary"].strip() != ""
