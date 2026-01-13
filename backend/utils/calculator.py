import csv

def bayesian_survival(prevalence, sensitivity, false_positive):
    """
    Calculate posterior probability using Bayes' Theorem.
    P(Disease | Positive) = (Sensitivity * Prevalence) /
                            [(Sensitivity * Prevalence) + (FalsePositive * (1 - Prevalence))]
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
# NEW: BayesCalculator Class for ML Integration
# ============================================================================

class BayesCalculator:
    """
    Bayesian probability calculator for disease prediction.
    Compatible with ML model integration.
    """
    
    def __init__(self):
        pass
    
    def calculate_posterior(self, prior, likelihood, false_positive_rate=0.05):
        """
        Calculate posterior probability using Bayes' Theorem.
        
        Args:
            prior: Prior probability (0-1)
            likelihood: P(symptoms|disease) - probability of symptoms given disease (0-1)
            false_positive_rate: P(symptoms|no disease) - probability of symptoms without disease (0-1)
        
        Returns:
            Dictionary with prior, likelihood, posterior, and false_positive_rate
        """
        try:
            prior = float(prior)
            likelihood = float(likelihood)
            false_positive_rate = float(false_positive_rate)
        except (TypeError, ValueError):
            raise ValueError(f"Non-numeric input provided")
        
        # Strict validation (do NOT silently fix values)
        for name, value in [("Prior probability", prior),("Likelihood", likelihood),("False positive rate", false_positive_rate)]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be between 0 and 1. Got {value}")

        # Bayes' Theorem: P(D|S) = P(S|D) * P(D) / P(S)
        # P(S) = P(S|D) * P(D) + P(S|~D) * P(~D)
        numerator = likelihood * prior
        denominator = numerator + (false_positive_rate * (1 - prior))
        
        if denominator == 0:
            posterior = 0.0
        else:
            posterior = numerator / denominator
        
        return {
            'prior': prior,
            'likelihood': likelihood,
            'posterior': posterior,
            'false_positive_rate': false_positive_rate
        }
    
    def calculate_with_test_result(self, prior, sensitivity, specificity, test_result='positive'):
        """
        Calculate posterior probability based on test result.
        
        Args:
            prior: Prior probability of disease (0-1)
            sensitivity: True positive rate (0-1)
            specificity: True negative rate (0-1)
            test_result: 'positive' or 'negative'
        
        Returns:
            Dictionary with calculation results
        """
        try:
            prior = float(prior)
            sensitivity = float(sensitivity)
            specificity = float(specificity)
        except (TypeError, ValueError):
            raise ValueError(f"Non-numeric input provided")
        
        for name, value in [("Prior probability", prior),("Sensitivity", sensitivity),("Specificity", specificity)]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be between 0 and 1. Got {value}")
        
        false_positive_rate = 1 - specificity
        
        if test_result.lower() == 'positive':
            # P(D|+) = P(+|D) * P(D) / [P(+|D) * P(D) + P(+|~D) * P(~D)]
            numerator = sensitivity * prior
            denominator = numerator + (false_positive_rate * (1 - prior))
        else:  # negative
            # P(D|-) = P(-|D) * P(D) / [P(-|D) * P(D) + P(-|~D) * P(~D)]
            numerator = (1 - sensitivity) * prior
            denominator = numerator + (specificity * (1 - prior))
        
        if denominator == 0:
            posterior = 0.0
        else:
            posterior = numerator / denominator
        
        return {
            'prior': prior,
            'sensitivity': sensitivity,
            'specificity': specificity,
            'false_positive_rate': false_positive_rate,
            'posterior': posterior,
            'test_result': test_result
        }


if __name__ == "__main__":
    data_file = 'C:\\Users\\Vansh\\Desktop\\October\\Projects\\disease_refactor\\hospital_data.csv'
    results = load_data(data_file)
    display_results(results)