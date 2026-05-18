import csv
import math

class BayesianDiagnosticCalculator:
    """
    A calculator that applies Bayes' Theorem to update disease probabilities
    based on clinical sensitivity, specificity, and prior prevalence.
    """
    
    @staticmethod
    def calculate_posterior(prior: float, sensitivity: float, false_positive_rate: float) -> dict:
        """
        Calculates the posterior probability P(A|B) using Bayes' Theorem.
        
        Args:
            prior (float): P(A) - Base rate/prevalence of the disease (0.0 to 1.0)
            sensitivity (float): P(B|A) - True Positive Rate (0.0 to 1.0)
            false_positive_rate (float): P(B|~A) - Type I Error Rate (0.0 to 1.0)
        """
        # Input validation guardrails
        if not all(0.0 <= x <= 1.0 for x in [prior, sensitivity, false_positive_rate]):
            raise ValueError("All probability inputs must be bounded between 0.0 and 1.0")
            
        # P(~A) = 1 - P(A)
        complement_prior = 1.0 - prior
        
        # Marginal likelihood / Evidence = P(B|A)*P(A) + P(B|~A)*P(~A)
        numerator = sensitivity * prior
        denominator = numerator + (false_positive_rate * complement_prior)
        
        # Handle edge case preventing division by zero
        if math.isclose(denominator, 0.0):
            posterior = 0.0
        else:
            posterior = numerator / denominator

        # Assign an educational risk stratification layer
        if posterior < 0.35:
            risk_category = "Low"
        elif 0.35 <= posterior < 0.70:
            risk_category = "Medium"
        else:
            risk_category = "High"
            
        return {
            "prior_probability": round(prior, 4),
            "posterior_probability": round(posterior, 4),
            "risk_tier": risk_category,
            "shift_magnitude": round(posterior - prior, 4)
        }

def bayesian_survival(prevalence, sensitivity, false_positive):
    """Fallback functional wrapper linking legacy code to class logic."""
    calc = BayesianDiagnosticCalculator()
    res = calc.calculate_posterior(float(prevalence), float(sensitivity), float(false_positive))
    return res["posterior_probability"]

def load_data(filepath):
    """Load hospital data from CSV and calculate posterior probabilities."""
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
    """Display the calculated posterior probabilities."""
    for result in results:
        specificity = 1 - float(result["FalsePositive"])
        print(
            f"Disease: {result['Disease']}, "
            f"Prevalence: {result['Prevalence']}, "
            f"Sensitivity: {result['Sensitivity']}, "
            f"Specificity: {specificity:.2f}, "
            f"Posterior: {result['Posterior']:.4f}"
        )

if __name__ == "__main__":
    data_file = 'hospital_data.csv'
    try:
        results = load_data(data_file)
        display_results(results)
    except Exception as e:
        pass