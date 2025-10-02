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


# second form of Bayes' Theorem

def second_form_of_bayes_theorem(prior_probability2, test_sensitivity2, p_b):
    
    """ Second form has P(B) which is P(positive in population or marginal likelihood) 
    Args : prior probability : P(A)
           test_sensitivity2: P(B|A) 
           p_b: when P(B) is known
           
    returns : P(A|B) or posterior probability
    """
    
    _assert_prob("prior_probability", prior_probability2)
    _assert_prob("test_sensitivity", test_sensitivity2)
    _assert_prob("p_b", p_b)
    
    numerator = test_sensitivity2 * prior_probability2
    denominator = p_b
    if denominator == 0:
        raise ValueError(
            "Inputs lead to an undefined calculation (division by zero). "
            "Try avoiding degenerate combinations (e.g., prior=0 with specificity=1 on a negative path, or similar)."
        )
    second_form_posterior_probability = numerator / denominator
    return second_form_posterior_probability


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

    return render_template("updated_index.html", result=result, error=error, values=form_values)

@app.route('/alternate', methods=['GET', 'POST'])
def alternate():
    error = None
    result = None
    # Pre-fill reasonable defaults for a quick demo
    defaults = {
        "prior_probability": "0.10",
        "test_sensitivity2": "0.90",
        "p_b": "0.25",

    }
    form_values = dict(defaults)
    
    if request.method == "POST":
        form_values["prior_probability2"] = request.form.get("prior_probability2", "").strip()
        form_values["test_sensitivity2"] = request.form.get("test_sensitivity2", "").strip()
        form_values["p_b"] = request.form.get("p_b", "").strip()


        try:
            prior = float(form_values["prior_probability2"])
            sens = float(form_values["test_sensitivity2"])
            p_b = float(form_values["p_b"])

            result = second_form_of_bayes_theorem(prior, sens, p_b)
            print(result)
        except ValueError as e:
            error = str(e)
        except Exception:
            error = "Unexpected error: please check your inputs."
            
    return render_template("index_Bayes_form2.html", result=result, error=error, values=form_values)

if __name__ == "__main__":
    app.run(debug=True)
