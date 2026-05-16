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
