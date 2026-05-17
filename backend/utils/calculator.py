import csv
import math

def bayesian_survival(prevalence, sensitivity, false_positive):
    """
    Calculate posterior probability using Bayes' Theorem.
    """
    try:
        prevalence = float(prevalence)
        sensitivity = float(sensitivity)
        false_positive = float(false_positive)
    except (TypeError, ValueError):
        raise ValueError("All inputs must be numeric")

    for name, value in [
        ("Prevalence", prevalence),
        ("Sensitivity", sensitivity),
        ("False positive rate", false_positive)
    ]:
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"{name} must be between 0 and 1. Got {value}")

    p_pos = (sensitivity * prevalence) + (false_positive * (1 - prevalence))
    if p_pos == 0:
        raise ValueError("Invalid inputs caused division by zero")

    posterior = (sensitivity * prevalence) / p_pos
    return posterior

def load_data(filepath):
    """
    Load hospital data from CSV and calculate posterior probabilities.
    """
    results = []
    with open(filepath, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            prevalence = float(row["Prevalence"])
            sensitivity = float(row["Sensitivity"])
            false_positive = float(row["FalsePositive"])
            posterior = bayesian_survival(prevalence, sensitivity, false_positive)
            row["Posterior"] = round(posterior, 4)
            results.append(row)
    return results

def display_results(results):
    """
    Display the posterior probabilities.
    """
    for result in results:
        specificity = 1 - float(result["FalsePositive"])
        print(
            f"Disease: {result['Disease']}, "
            f"Prevalence: {result['Prevalence']}, "
            f"Sensitivity: {result['Sensitivity']}, "
            f"Specificity: {specificity:.2f}, "
            f"Posterior: {result['Posterior']:.4f}"
        )


# ============================================================================
# UPGRADED: BayesCalculator Class for ML Integration (Netlify & Frontend Sync)
# ============================================================================

class BayesCalculator:
    """
    Bayesian probability calculator for disease prediction.
    Enhanced with data types, risk stratification, and backwards compatibility.
    """
    
    def __init__(self):
        pass

    def calculate_posterior(self, prior: float, likelihood: float, false_positive_rate: float = 0.05) -> dict:
        """
        Calculates the posterior probability using Bayes' Theorem for ML models.
        """
        try:
            prior = float(prior)
            likelihood = float(likelihood)
            false_positive_rate = float(false_positive_rate)
        except (TypeError, ValueError):
            raise ValueError("Non-numeric input provided")

        for name, value in [("Prior probability", prior), ("Likelihood", likelihood), ("False positive rate", false_positive_rate)]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be between 0 and 1. Got {value}")

        complement_prior = 1.0 - prior
        numerator = likelihood * prior
        denominator = numerator + (false_positive_rate * complement_prior)

        if math.isclose(denominator, 0.0):
            posterior = 0.0
        else:
            posterior = numerator / denominator

        if posterior < 0.35:
            risk_category = "Low"
        elif 0.35 <= posterior < 0.70:
            risk_category = "Medium"
        else:
            risk_category = "High"

        return {
            # Legacy fields (Keeps existing frontend components working perfectly)
            'prior': round(prior, 4),
            'likelihood': round(likelihood, 4),
            'posterior': round(posterior, 4),
            'false_positive_rate': round(false_positive_rate, 4),
            # New Advanced Data Science Fields
            "prior_probability": round(prior, 4),
            "posterior_probability": round(posterior, 4),
            "risk_tier": risk_category,
            "shift_magnitude": round(posterior - prior, 4)
        }

    def calculate_with_test_result(self, prior: float, sensitivity: float, specificity: float, test_result: str = 'positive') -> dict:
        """
        Calculate posterior probability based on diagnostic test result.
        """
        try:
            prior = float(prior)
            sensitivity = float(sensitivity)
            specificity = float(specificity)
        except (TypeError, ValueError):
            raise ValueError("Non-numeric input provided")

        for name, value in [("Prior probability", prior), ("Sensitivity", sensitivity), ("Specificity", specificity)]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be between 0 and 1. Got {value}")

        false_positive_rate = 1.0 - specificity

        if str(test_result).lower() == 'positive':
            numerator = sensitivity * prior
            denominator = numerator + (false_positive_rate * (1.0 - prior))
        else:
            numerator = (1.0 - sensitivity) * prior
            denominator = numerator + (specificity * (1.0 - prior))

        if math.isclose(denominator, 0.0):
            posterior = 0.0
        else:
            posterior = numerator / denominator

        if posterior < 0.35:
            risk_category = "Low"
        elif 0.35 <= posterior < 0.70:
            risk_category = "Medium"
        else:
            risk_category = "High"

        return {
            # Legacy fields (Keeps existing frontend components working perfectly)
            'prior': round(prior, 4),
            'sensitivity': round(sensitivity, 4),
            'specificity': round(specificity, 4),
            'false_positive_rate': round(false_positive_rate, 4),
            'posterior': round(posterior, 4),
            'test_result': test_result,
            # New Advanced Data Science Fields
            "prior_probability": round(prior, 4),
            "posterior_probability": round(posterior, 4),
            "risk_tier": risk_category,
            "shift_magnitude": round(posterior - prior, 4)
        }


if __name__ == "__main__":
    pass
