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
    # prior=0, spec=1, positive branch: denominator = 0*(1-0) = 0
    with pytest.raises(ValueError):
        bayes_theorem(0.0, 0.9, 1.0, "positive")


def test_alias_matches_main():
    v1 = bayes_theorem(0.1, 0.9, 0.95, "positive")
    v2 = survival_chance(0.1, 0.9, 0.95, "positive")
    assert v1 == v2


# ---------- type errors ----------

@pytest.mark.parametrize("args", [
    ("0.1", 0.9, 0.95, "positive"),
    (0.1, "0.9", 0.95, "positive"),
    (0.1, 0.9, "0.95", "positive"),
    (0.1, 0.9, 0.95, 123),
    (None, 0.9, 0.95, "positive"),
    (0.1, None, 0.95, "positive"),
    (0.1, 0.9, None, "positive"),
    (0.1, 0.9, 0.95, None),
])
def test_type_errors(args):
    with pytest.raises(Exception):
        bayes_theorem(*args)


# ---------- positive test-result branch ----------

def test_typical_valid_cases():
    # P(D|+) = sens*prior / (sens*prior + (1-spec)*(1-prior))
    assert round(bayes_theorem(0.01, 0.99, 0.95, "positive"), 4) == 0.1667
    assert round(bayes_theorem(0.10, 0.90, 0.90, "positive"), 4) == 0.5
    assert round(bayes_theorem(0.20, 0.85, 0.80, "positive"), 4) == 0.5152


def test_high_specificity():
    assert round(bayes_theorem(0.15, 0.75, 0.99, "positive"), 4) == 0.9298


def test_high_sensitivity():
    assert round(bayes_theorem(0.15, 0.99, 0.75, "positive"), 4) == 0.4114


def test_mid_range_probabilities():
    assert round(bayes_theorem(0.5, 0.5, 0.5, "positive"), 4) == 0.5
    assert round(bayes_theorem(0.3, 0.7, 0.6, "positive"), 4) == 0.4286


def test_float_precision():
    assert round(bayes_theorem(0.1234, 0.5678, 0.9101, "positive"), 4) == 0.4707


def test_high_probabilities():
    assert round(bayes_theorem(0.99, 0.99, 0.99, "positive"), 4) == 0.9999
    assert round(bayes_theorem(0.95, 0.95, 0.95, "positive"), 4) == 0.9972


def test_low_probabilities():
    assert (
        round(bayes_theorem(0.01, 0.01, 0.01, "positive"), 4) == 0.0099
    )
    assert (
        round(bayes_theorem(0.05, 0.05, 0.05, "positive"), 4) == 0.0526
    )

def test_high_probabilities_duplicate():
    assert round(bayes_theorem(0.99, 0.99, 0.99, "positive"), 4) == 0.99
    assert round(bayes_theorem(0.95, 0.95, 0.95, "positive"), 4) == 0.95
