import numpy as np
import pandas as pd

class BayesCalculator:
    def __init__(self, fallback_prior=0.01):
        """
        Initializes the calculator with a fallback prior probability for cases
        where exact baseline data is missing.
        """
        self.fallback_prior = fallback_prior

    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Loads epidemiology or clinical trial data from a CSV file.
        """
        try:
            return pd.read_csv(filepath)
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()

    def calculate_posterior(self, prior: float, sensitivity: float, specificity: float, condition_present: bool = True) -> float:
        """
        Calculates the single-stage posterior probability using Bayes' Theorem.
        """
        # Multi-symptom input validation boundaries
        if not (0 <= prior <= 1 and 0 <= sensitivity <= 1 and 0 <= specificity <= 1):
            raise ValueError("Probabilities must be securely bounded between 0.0 and 1.0 inclusive.")

        if condition_present:
            numerator = sensitivity * prior
            denominator = (sensitivity * prior) + ((1 - specificity) * (1 - prior))
        else:
            numerator = (1 - sensitivity) * prior
            denominator = ((1 - 1) * prior) + (specificity * (1 - prior))

        if denominator == 0:
            return 0.0
            
        return float(numerator / denominator)

    def calculate_with_test_result(self, prior: float, sensitivity: float, specificity: float, test_result: str = 'positive') -> dict:
        """
        Calculates diagnostic updates conditionally evaluating clinical test binary matrix outcomes.
        """
        is_positive = test_result.lower() == 'positive'
        posterior = self.calculate_posterior(prior, sensitivity, specificity, condition_present=is_positive)
        
        # Dynamic three-tier risk stratification matrix based on posterior trend shifts
        if posterior < 0.35:
            risk_tier = "Low"
        elif posterior < 0.70:
            risk_tier = "Medium"
        else:
            risk_tier = "High"

        shift_magnitude = float(posterior - prior)

        return {
            "posterior": round(posterior, 4),
            "risk_tier": risk_tier,
            "shift_magnitude": round(shift_magnitude, 4)
        }

    def bayesian_survival(self, hazard_ratio: float, baseline_survival: float) -> float:
        """
        Estimates adjusted conditional survival probabilities given specific diagnostic hazard indicators.
        """
        if not (0 <= baseline_survival <= 1):
            raise ValueError("Baseline survival must be between 0.0 and 1.0 inclusive.")
        
        # S(t) = S0(t)^exp(beta) matching baseline proportional hazard models
        adjusted_survival = np.power(baseline_survival, hazard_ratio)
        return float(round(adjusted_survival, 4))

    def display_results(self, metrics: dict) -> None:
        """
        Utility endpoint operation to format clean evaluation logs.
        """
        print("\n--- Bayesian Diagnostic Evaluation ---")
        for key, value in metrics.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print("--------------------------------------")
