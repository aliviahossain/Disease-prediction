
from backend import create_app

app = create_app()


def _assert_prob(name: str, value: float):
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"{name} must be between 0 and 1 (inclusive). Got {value}.")


def bayes_theorem(prior_probability, test_sensitivity, test_specificity, test_result):
    """
    Calculate the posterior probability of disease given a test result,
    using Bayes' theorem, with input validation.
    """
    _assert_prob("prior_probability", prior_probability)
    _assert_prob("test_sensitivity", test_sensitivity)
    _assert_prob("test_specificity", test_specificity)

    if test_result not in {"positive", "negative"}:
        raise ValueError('test_result must be either "positive" or "negative".')

    if test_result == "positive":
        numerator = test_sensitivity * prior_probability
        denominator = numerator + (1 - test_specificity) * (1 - prior_probability)
    else:  # negative
        numerator = (1 - test_sensitivity) * prior_probability
        denominator = numerator + test_specificity * (1 - prior_probability)

    if denominator == 0:
        raise ValueError("Inputs lead to an undefined calculation (division by zero).")

    return numerator / denominator


def survival_chance(prior, sensitivity, specificity, test_result):
    return bayes_theorem(prior, sensitivity, specificity, test_result)


if __name__ == "__main__":
    app.run(debug=True)
