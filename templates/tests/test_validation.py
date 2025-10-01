import pytest
from app import bayes_theorem, survival_chance

def test_valid_bounds_positive():
    assert 0 <= bayes_theorem(0.1, 0.9, 0.95, "positive") <= 1

def test_valid_bounds_negative():
    assert 0 <= bayes_theorem(0.1, 0.9, 0.95, "negative") <= 1

@pytest.mark.parametrize("prior", [-0.1, 1.1])
def test_prior_out_of_bounds(prior):
    with pytest.raises(ValueError):
        bayes_theorem(prior, 0.9, 0.95, "positive")

@pytest.mark.parametrize("sens", [-0.01, 1.01])
def test_sensitivity_out_of_bounds(sens):
    with pytest.raises(ValueError):
        bayes_theorem(0.1, sens, 0.95, "positive")

@pytest.mark.parametrize("spec", [-0.2, 1.2])
def test_specificity_out_of_bounds(spec):
    with pytest.raises(ValueError):
        bayes_theorem(0.1, 0.9, spec, "positive")

def test_invalid_test_result():
    with pytest.raises(ValueError):
        bayes_theorem(0.1, 0.9, 0.95, "posi-tive")  # typo

def test_division_by_zero_guard():
    # Construct a degenerate case where denominator would be zero
    # For negative branch: numerator=(1-sens)*prior, denominator=numerator + spec*(1-prior)
    # If prior=0 and spec=1 and test_result='negative' -> denom = 0 + 1*(1-0)=1 (safe)
    # For positive branch: prior=0, spec=1 -> denom=(1-1)*(1-0)=0 (since numerator=0 as well) -> 0
    with pytest.raises(ValueError):
        bayes_theorem(0.0, 0.9, 1.0, "positive")

def test_alias_matches_main():
    v1 = bayes_theorem(0.1, 0.9, 0.95, "positive")
    v2 = survival_chance(0.1, 0.9, 0.95, "positive")
    assert v1 == v2
