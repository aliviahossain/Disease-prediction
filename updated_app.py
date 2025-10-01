from flask import Flask, render_template, request
app = Flask(__name__)

def _assert_prob(name: str, value: float):
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"{name} must be between 0 and 1 (inclusive). Got {value}.")

def bayes_theorem(prior_probability, test_sensitivity, test_specificity, test_result):
    """
    Calculate the posterior probability of disease given a test result,
    using Bayes' theorem, with input validation.

    Args:
        prior_probability (float): baseline probability of disease (0–1)
        test_sensitivity (float): P(test+ | disease) (0–1)
        test_specificity (float): P(test- | no disease) (0–1)
        test_result (str): "positive" or "negative"

    Returns:
        float: posterior probability of disease given the test result
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
        raise ValueError(
            "Inputs lead to an undefined calculation (division by zero). "
            "Try avoiding degenerate combinations (e.g., prior=0 with specificity=1 on a negative path, or similar)."
        )

    posterior_probability = numerator / denominator
    return posterior_probability


# Backwards-compatible alias
def survival_chance(prior, sensitivity, specificity, test_result):
    """Deprecated alias for bayes_theorem (kept for backwards compatibility)."""
    return bayes_theorem(prior, sensitivity, specificity, test_result)


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    result = None
    # Pre-fill reasonable defaults for a quick demo
    defaults = {
        "prior_probability": "0.10",
        "test_sensitivity": "0.90",
        "test_specificity": "0.95",
        "test_result": "positive",
    }

    form_values = dict(defaults)

    if request.method == "POST":
        form_values["prior_probability"] = request.form.get("prior_probability", "").strip()
        form_values["test_sensitivity"] = request.form.get("test_sensitivity", "").strip()
        form_values["test_specificity"] = request.form.get("test_specificity", "").strip()
        form_values["test_result"] = request.form.get("test_result", "").strip().lower()

        try:
            prior = float(form_values["prior_probability"])
            sens = float(form_values["test_sensitivity"])
            spec = float(form_values["test_specificity"])
            test_res = form_values["test_result"]

            result = bayes_theorem(prior, sens, spec, test_res)

        except ValueError as e:
            error = str(e)
        except Exception:
            error = "Unexpected error: please check your inputs."

    return render_template("index.html", result=result, error=error, values=form_values)


if __name__ == "__main__":
    app.run(debug=True)
