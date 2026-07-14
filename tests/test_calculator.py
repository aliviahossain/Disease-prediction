import pytest
from backend.utils.calculator import BayesCalculator, bayesian_survival


# ── bayesian_survival ────────────────────────────────────────────────────────

def test_bayesian_survival_basic():
    result = bayesian_survival(0.01, 0.9, 0.05)
    assert 0.0 < result < 1.0


def test_bayesian_survival_high_prevalence():
    result = bayesian_survival(0.9, 0.95, 0.1)
    assert result > 0.9


def test_bayesian_survival_low_prevalence():
    result = bayesian_survival(0.001, 0.99, 0.05)
    assert result < 0.1


def test_bayesian_survival_boundary_zero_prevalence():
    result = bayesian_survival(0.0, 0.9, 0.05)
    assert result == 0.0


def test_bayesian_survival_boundary_full_prevalence():
    result = bayesian_survival(1.0, 0.9, 0.05)
    assert result == 1.0


def test_bayesian_survival_invalid_prevalence():
    with pytest.raises(ValueError):
        bayesian_survival(1.5, 0.9, 0.05)


def test_bayesian_survival_invalid_sensitivity():
    with pytest.raises(ValueError):
        bayesian_survival(0.1, -0.1, 0.05)


def test_bayesian_survival_invalid_false_positive():
    with pytest.raises(ValueError):
        bayesian_survival(0.1, 0.9, 1.5)


def test_bayesian_survival_non_numeric():
    with pytest.raises(ValueError):
        bayesian_survival("high", 0.9, 0.05)


def test_bayesian_survival_zero_division():
    with pytest.raises(ValueError):
        bayesian_survival(0.0, 0.0, 0.0)


# ── BayesCalculator ──────────────────────────────────────────────────────────

@pytest.fixture
def calc():
    return BayesCalculator()


def test_calculate_posterior_basic(calc):
    result = calc.calculate_posterior(0.1, 0.8, 0.05)
    assert "posterior" in result
    assert 0.0 <= result["posterior"] <= 1.0


def test_calculate_posterior_risk_low(calc):
    result = calc.calculate_posterior(0.01, 0.1, 0.5)
    assert result["risk_tier"] == "Low"


def test_calculate_posterior_risk_medium(calc):
    result = calc.calculate_posterior(0.5, 0.55, 0.3)
    assert result["risk_tier"] == "Medium"


def test_calculate_posterior_risk_high(calc):
    result = calc.calculate_posterior(0.9, 0.95, 0.05)
    assert result["risk_tier"] == "High"


def test_calculate_posterior_shift_magnitude(calc):
    result = calc.calculate_posterior(0.2, 0.8, 0.05)
    assert result["shift_magnitude"] == round(
        result["posterior"] - result["prior"], 4
    )


def test_calculate_posterior_invalid_prior(calc):
    with pytest.raises(ValueError):
        calc.calculate_posterior(-0.1, 0.8, 0.05)


def test_calculate_posterior_non_numeric(calc):
    with pytest.raises(ValueError):
        calc.calculate_posterior("high", 0.8, 0.05)


def test_calculate_with_test_result_positive(calc):
    result = calc.calculate_with_test_result(0.1, 0.9, 0.95, "positive")
    assert result["posterior"] > result["prior"]


def test_calculate_with_test_result_negative(calc):
    result = calc.calculate_with_test_result(0.5, 0.9, 0.95, "negative")
    assert result["posterior"] < result["prior"]


def test_calculate_with_test_result_legacy_fields(calc):
    result = calc.calculate_with_test_result(0.1, 0.9, 0.95, "positive")
    assert "prior" in result
    assert "sensitivity" in result
    assert "specificity" in result
    assert "posterior" in result