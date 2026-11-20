"""
Bayesian probability calculations — the single source of truth.

* bayesian_survival()          — posterior from prevalence / sensitivity /
                                 false-positive rate (used by the web calculator)
* bayes_theorem()              — posterior for a positive OR negative test result
                                 from prior / sensitivity / specificity
* posterior_given_positive()   — prior / sensitivity / specificity, positive test
* BayesCalculator              — ML integration (risk tiers, order invariance)
* load_data() / display_results() — batch processing of prior/sensitivity/
                                 specificity CSV files
"""

import itertools
import math

import pandas as pd


def clamp_probability(
    value: float, min_val: float = 0.0, max_val: float = 1.0
) -> float:
    """
    Clamp a probability value to the range [min_val, max_val].
    Ensures probability values stay within valid bounds [0.0, 1.0].
    Useful for handling floating-point precision errors in Bayesian calculations.
    """
    return max(min_val, min(max_val, value))


# Tolerance for floating-point noise (e.g. an ML model returning 1.0000000002).
_PROBABILITY_TOLERANCE = 1e-6


def validate_probability(value: float, name: str = "probability") -> float:
    """
    Reject clearly invalid probabilities, but clamp tiny floating-point
    overshoots back into [0, 1]. Silently clamping real input errors such as
    -0.1 or 1.5 would hide bugs and produce misleading posteriors.
    """
    if not (-_PROBABILITY_TOLERANCE <= value <= 1.0 + _PROBABILITY_TOLERANCE):
        raise ValueError(f"{name} must be between 0 and 1. Got {value}")
    return clamp_probability(value)


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
        ("False positive rate", false_positive),
    ]:
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"{name} must be between 0 and 1. Got {value}")

    p_pos = (sensitivity * prevalence) + (false_positive * (1 - prevalence))
    if p_pos == 0:
        raise ValueError("Invalid inputs caused division by zero")

    posterior = (sensitivity * prevalence) / p_pos
    return posterior


def bayes_theorem(prior_probability, test_sensitivity, test_specificity, test_result):
    """Posterior probability of disease given a "positive" or "negative" test."""
    validate_probability(prior_probability, "prior_probability")
    validate_probability(test_sensitivity, "test_sensitivity")
    validate_probability(test_specificity, "test_specificity")

    if test_result not in {"positive", "negative"}:
        raise ValueError('test_result must be either "positive" or "negative".')

    if test_result == "positive":
        numerator = test_sensitivity * prior_probability
        denominator = numerator + (1 - test_specificity) * (1 - prior_probability)
    else:
        numerator = (1 - test_sensitivity) * prior_probability
        denominator = numerator + test_specificity * (1 - prior_probability)

    if denominator == 0:
        raise ValueError("Inputs lead to an undefined calculation (division by zero).")
    return numerator / denominator


def survival_chance(prior, sensitivity, specificity, test_result):
    """Backwards-compatible alias for bayes_theorem()."""
    return bayes_theorem(prior, sensitivity, specificity, test_result)


def posterior_given_positive(prior, sensitivity, specificity):
    """P(disease | positive test) from prior, sensitivity and specificity.

    Returns 0.0 (instead of raising) when the evidence has zero probability.
    """
    try:
        prior = float(prior)
        sensitivity = float(sensitivity)
        specificity = float(specificity)
    except (TypeError, ValueError):
        raise ValueError(
            f"Non-numeric input: prior={prior}, sensitivity={sensitivity}, "
            f"specificity={specificity}"
        )

    prior = validate_probability(prior, "prior")
    sensitivity = validate_probability(sensitivity, "sensitivity")
    specificity = validate_probability(specificity, "specificity")

    evidence = (sensitivity * prior) + ((1 - specificity) * (1 - prior))
    if evidence == 0:
        return 0.0
    return (sensitivity * prior) / evidence


# ----------------------------------------------------------------------------
# Batch processing of CSV files with prior / sensitivity / specificity columns
# ----------------------------------------------------------------------------
_BATCH_COLUMNS = ["prior", "sensitivity", "specificity"]


def read_data(filepath):
    """Read a batch CSV; an empty file yields an empty frame."""
    try:
        df = pd.read_csv(filepath)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=_BATCH_COLUMNS)
    if not set(_BATCH_COLUMNS).issubset(df.columns):
        raise ValueError(
            f"CSV must contain columns: {set(_BATCH_COLUMNS)}, "
            f"found {df.columns.tolist()}"
        )
    return df


def clean_data(df, strict=False):
    """Coerce to numbers, clip to [0, 1], and drop (or reject) invalid rows."""
    df = df.copy()
    df[_BATCH_COLUMNS] = df[_BATCH_COLUMNS].apply(pd.to_numeric, errors="coerce")
    df[_BATCH_COLUMNS] = df[_BATCH_COLUMNS].clip(0, 1)

    nan_mask = df[_BATCH_COLUMNS].isna().any(axis=1)
    if strict:
        if nan_mask.any():
            raise ValueError(f"Invalid rows found:\n{df[nan_mask]}")
        return df

    dropped_count = nan_mask.sum()
    if dropped_count > 0:
        print(
            f"Warning: Dropped {dropped_count} invalid row(s) due to non-numeric values."
        )
    return df[~nan_mask]


def add_posterior_column(df):
    """Add a 'posterior' column (0.0 where the evidence probability is zero)."""
    df = df.copy()
    numerator = df["sensitivity"] * df["prior"]
    denominator = numerator + ((1 - df["specificity"]) * (1 - df["prior"]))
    df["posterior"] = numerator / denominator
    df.loc[denominator == 0, "posterior"] = 0.0
    return df


def load_data(filepath, strict=False, save_results_flag=False, save_path=None):
    """Load a batch CSV and return its rows with posterior probabilities."""
    df = add_posterior_column(clean_data(read_data(filepath), strict=strict))

    if save_results_flag:
        if save_path is None:
            raise ValueError("save_path must be provided if save_results_flag=True")
        if df.empty:
            raise ValueError("No valid rows to save after data cleaning.")
        df.to_csv(save_path, index=False)

    return df.to_dict(orient="records")


def display_results(results):
    """Print batch results to the console."""
    for row in results:
        print(
            f"Prior: {row['prior']}, Sensitivity: {row['sensitivity']}, "
            f"Specificity: {row['specificity']}, Posterior: {row['posterior']:.4f}"
        )


# ============================================================================
# BayesCalculator: ML integration
# ============================================================================


class BayesCalculator:
    """
    Bayesian probability calculator for disease prediction.
    Enhanced with data types, risk stratification, and backwards compatibility.
    """

    def __init__(self):
        pass

    def _compute_posterior_value(
        self, prior: float, likelihood: float, false_positive_rate: float = 0.05
    ) -> float:
        """Compute the raw posterior value without rounding, clamped to [0, 1]."""
        complement_prior = 1.0 - prior
        numerator = likelihood * prior
        denominator = numerator + (false_positive_rate * complement_prior)
        if math.isclose(denominator, 0.0):
            return 0.0
        posterior = numerator / denominator
        return clamp_probability(posterior)

    def calculate_posterior(
        self, prior: float, likelihood: float, false_positive_rate: float = 0.05
    ) -> dict:
        """
        Calculates the posterior probability using Bayes' Theorem for ML models.
        Rejects out-of-range probabilities; clamps tiny float overshoots.
        """
        try:
            prior = float(prior)
            likelihood = float(likelihood)
            false_positive_rate = float(false_positive_rate)
        except (TypeError, ValueError):
            raise ValueError("Non-numeric input provided")

        prior = validate_probability(prior, "prior")
        likelihood = validate_probability(likelihood, "likelihood")
        false_positive_rate = validate_probability(
            false_positive_rate, "false_positive_rate"
        )

        posterior = self._compute_posterior_value(
            prior, likelihood, false_positive_rate
        )

        if posterior < 0.35:
            risk_category = "Low"
        elif 0.35 <= posterior < 0.70:
            risk_category = "Medium"
        else:
            risk_category = "High"

        return {
            # Legacy fields (Keeps existing frontend components working perfectly)
            "prior": round(prior, 4),
            "likelihood": round(likelihood, 4),
            "posterior": round(posterior, 4),
            "false_positive_rate": round(false_positive_rate, 4),
            # New Advanced Data Science Fields
            "prior_probability": round(prior, 4),
            "posterior_probability": round(posterior, 4),
            "risk_tier": risk_category,
            "shift_magnitude": round(posterior - prior, 4),
        }

    def verify_order_invariance(
        self,
        model,
        disease: str,
        symptoms: list,
        tolerance: float = 1e-6,
        max_permutations: int = 6,
    ) -> dict:
        """Verify Bayesian posterior stability across symptom order permutations."""
        if symptoms is None:
            symptoms = []

        ordered_sequences = []
        seen = set()
        for perm in itertools.islice(itertools.permutations(symptoms), None):
            if perm in seen:
                continue
            seen.add(perm)
            ordered_sequences.append(list(perm))
            if len(ordered_sequences) >= max_permutations:
                break

        if not ordered_sequences:
            return {
                "order_invariant": True,
                "tested_orderings": 0,
                "posterior_drift": 0.0,
                "max_posterior": 0.0,
                "min_posterior": 0.0,
                "posterior_values": [],
                "diagnostic": "No symptoms provided; order invariance holds by definition.",
            }

        baseline_order = ordered_sequences[0]
        baseline_prediction = model.predict_disease_probability(disease, baseline_order)
        baseline_posterior = self._compute_posterior_value(
            baseline_prediction["prior_probability"],
            baseline_prediction["likelihood"],
            0.05,
        )

        posterior_values = [baseline_posterior]
        drift_records = []
        for seq in ordered_sequences[1:]:
            prediction = model.predict_disease_probability(disease, seq)
            posterior = self._compute_posterior_value(
                prediction["prior_probability"],
                prediction["likelihood"],
                0.05,
            )
            posterior_values.append(posterior)
            drift_records.append(
                {
                    "symptom_order": seq,
                    "posterior": round(posterior, 8),
                    "drift": round(abs(posterior - baseline_posterior), 8),
                }
            )

        max_posterior = max(posterior_values)
        min_posterior = min(posterior_values)
        max_drift = max_posterior - min_posterior
        invariant = max_drift <= tolerance

        return {
            "order_invariant": invariant,
            "tested_orderings": len(ordered_sequences),
            "posterior_drift": round(max_drift, 8),
            "max_posterior": round(max_posterior, 8),
            "min_posterior": round(min_posterior, 8),
            "posterior_values": [round(p, 8) for p in posterior_values],
            "diagnostic": (
                "Posterior probability remained stable across symptom orderings."
                if invariant
                else "Detected non-commutative posterior drift across symptom orderings."
            ),
            "tolerance": tolerance,
            "drift_records": drift_records,
        }

    def calculate_with_test_result(
        self,
        prior: float,
        sensitivity: float,
        specificity: float,
        test_result: str = "positive",
    ) -> dict:
        """
        Calculate posterior probability based on diagnostic test result.
        Rejects out-of-range probabilities; clamps tiny float overshoots.
        """
        try:
            prior = float(prior)
            sensitivity = float(sensitivity)
            specificity = float(specificity)
        except (TypeError, ValueError):
            raise ValueError("Non-numeric input provided")

        # Clamp all probability inputs to valid [0, 1] range
        # This handles floating-point precision errors from ML models
        prior = validate_probability(prior, "prior")
        sensitivity = validate_probability(sensitivity, "sensitivity")
        specificity = validate_probability(specificity, "specificity")

        false_positive_rate = 1.0 - specificity

        if str(test_result).lower() == "positive":
            numerator = sensitivity * prior
            denominator = numerator + (false_positive_rate * (1.0 - prior))
        else:
            numerator = (1.0 - sensitivity) * prior
            denominator = numerator + (specificity * (1.0 - prior))

        if math.isclose(denominator, 0.0):
            posterior = 0.0
        else:
            posterior = numerator / denominator

        # Clamp posterior to valid [0, 1] range
        posterior = clamp_probability(posterior)

        if posterior < 0.35:
            risk_category = "Low"
        elif 0.35 <= posterior < 0.70:
            risk_category = "Medium"
        else:
            risk_category = "High"

        return {
            # Legacy fields (Keeps existing frontend components working perfectly)
            "prior": round(prior, 4),
            "sensitivity": round(sensitivity, 4),
            "specificity": round(specificity, 4),
            "false_positive_rate": round(false_positive_rate, 4),
            "posterior": round(posterior, 4),
            "test_result": test_result,
            # New Advanced Data Science Fields
            "prior_probability": round(prior, 4),
            "posterior_probability": round(posterior, 4),
            "risk_tier": risk_category,
            "shift_magnitude": round(posterior - prior, 4),
        }


if __name__ == "__main__":
    pass
