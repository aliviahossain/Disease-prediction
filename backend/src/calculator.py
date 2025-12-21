import pandas as pd

def bayesian_survival(prior, sensitivity, specificity):
    """
    Calculate posterior probability using Bayes' Theorem.
    
    Args:
        prior: Prior probability of disease (0-1)
        sensitivity: True positive rate (0-1)
        specificity: True negative rate (0-1)
    
    Returns:
        Posterior probability of disease given positive test result
    """
    try:
        prior = float(prior)
        sensitivity = float(sensitivity)
        specificity = float(specificity)
    except (TypeError, ValueError):
        raise ValueError(f"Non-numeric input: prior={prior}, sensitivity={sensitivity}, specificity={specificity}")

    prior = max(0.0, min(1.0, prior))
    sensitivity = max(0.0, min(1.0, sensitivity))
    specificity = max(0.0, min(1.0, specificity))

    likelihood = (sensitivity * prior) + ((1 - specificity) * (1 - prior))
    if likelihood == 0:
        return 0.0
    return (sensitivity * prior) / likelihood


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
        
        # Clamp values to [0, 1]
        prior = max(0.0, min(1.0, prior))
        likelihood = max(0.0, min(1.0, likelihood))
        false_positive_rate = max(0.0, min(1.0, false_positive_rate))
        
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
        
        # Clamp values
        prior = max(0.0, min(1.0, prior))
        sensitivity = max(0.0, min(1.0, sensitivity))
        specificity = max(0.0, min(1.0, specificity))
        
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


def read_data(filepath):
    """Read CSV data for batch processing"""
    df = pd.read_csv(filepath)
    expected_cols = {'prior', 'sensitivity', 'specificity'}
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {expected_cols}, found {df.columns.tolist()}")
    return df


def clean_data(df, strict=False):
    """Clean and validate data"""
    df = df.copy()
    df[["prior", "sensitivity", "specificity"]] = df[["prior", "sensitivity", "specificity"]].apply(pd.to_numeric, errors='coerce')
    df[["prior", "sensitivity", "specificity"]] = df[["prior", "sensitivity", "specificity"]].clip(0, 1)

    nan_mask = df[["prior", "sensitivity", "specificity"]].isna().any(axis=1)

    if strict:
        if nan_mask.any():
            bad_rows = df[nan_mask]
            raise ValueError(f"Invalid rows found:\n{bad_rows}")
        return df
    else:
        dropped_count = nan_mask.sum()
        if dropped_count > 0:
            print(f"Warning: Dropped {dropped_count} invalid row(s) due to non-numeric values.")
        return df[~nan_mask]


def add_posterior_column(df):
    """Add posterior probability column to dataframe"""
    df = df.copy()

    numerator = df['sensitivity'] * df['prior']
    denominator = numerator + ((1 - df['specificity']) * (1 - df['prior']))

    # Avoid division by zero: where denominator == 0, set posterior = 0
    df['posterior'] = numerator / denominator
    df.loc[denominator == 0, 'posterior'] = 0.0

    return df


def save_results(df, save_path):
    """Save results to CSV"""
    df.to_csv(save_path, index=False)


def load_data(filepath, strict=False, save_results_flag=False, save_path=None):
    """Load and process data from CSV"""
    df = read_data(filepath)
    df = clean_data(df, strict=strict)
    df = add_posterior_column(df)

    if save_results_flag:
        if save_path is None:
            raise ValueError("save_path must be provided if save_results_flag=True")
        save_results(df, save_path)

    return df.to_dict(orient='records')


def display_results(results):
    """Display results in console"""
    for row in results:
        print(
            f"Prior: {row['prior']}, Sensitivity: {row['sensitivity']}, "
            f"Specificity: {row['specificity']}, Posterior: {row['posterior']:.4f}"
        )


if __name__ == "__main__":
    data_file = 'data/hospital_data.csv'
    try:
        results = load_data(data_file)
        display_results(results)
    except Exception as e:
        print(f"Error: {e}")