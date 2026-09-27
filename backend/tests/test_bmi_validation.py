from backend.models.ml_model import ml_model


def test_bmi_is_none_for_zero_height():
    assert ml_model._calculate_bmi(0, 70) is None


def test_bmi_is_none_for_zero_weight():
    assert ml_model._calculate_bmi(170, 0) is None


def test_bmi_is_none_for_negative_height():
    assert ml_model._calculate_bmi(-170, 70) is None


def test_bmi_is_none_for_negative_weight():
    assert ml_model._calculate_bmi(170, -70) is None


def test_bmi_is_none_for_missing_values():
    assert ml_model._calculate_bmi(None, 70) is None
    assert ml_model._calculate_bmi(170, None) is None


def test_bmi_is_none_for_non_numeric_values():
    assert ml_model._calculate_bmi("abc", 70) is None
    assert ml_model._calculate_bmi(170, "abc") is None


def test_bmi_is_none_outside_physiological_bounds():
    assert ml_model._calculate_bmi(20, 70) is None  # below 30 cm
    assert ml_model._calculate_bmi(300, 70) is None  # above 272 cm
    assert ml_model._calculate_bmi(170, 700) is None  # above 635 kg


def test_bmi_computes_correctly_for_valid_input():
    bmi = ml_model._calculate_bmi(170, 70)
    assert bmi is not None
    assert round(bmi, 2) == 24.22


def test_predict_disease_probability_does_not_crash_on_zero_height():
    # Regression test for issue #593: a height of 0 must no longer raise
    # ZeroDivisionError, and the resulting probability must not be negative.
    result = ml_model.predict_disease_probability(
        "diabetes",
        ["increased_thirst", "fatigue"],
        age=30,
        height_cm=0,
        weight_kg=70,
    )
    assert result["bmi"] is None
    assert result["calibrated_probability"] >= 0


def test_predict_disease_probability_does_not_crash_on_negative_weight():
    result = ml_model.predict_disease_probability(
        "diabetes",
        ["increased_thirst", "fatigue"],
        age=30,
        height_cm=170,
        weight_kg=-70,
    )
    assert result["bmi"] is None
    assert result["calibrated_probability"] >= 0
