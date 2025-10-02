import pandas as pd

def bayesian_survival(prior, sensitivity, specificity):
    """
    Compute posterior probability using Bayes' theorem.
    """
    # Type coercion
    try:
        prior = float(prior)
        sensitivity = float(sensitivity)
        specificity = float(specificity)
    except (TypeError, ValueError):
        raise ValueError(f"Non-numeric input: prior={prior}, sensitivity={sensitivity}, specificity={specificity}")

    # Clip to valid range
    prior = max(0.0, min(1.0, prior))
    sensitivity = max(0.0, min(1.0, sensitivity))
    specificity = max(0.0, min(1.0, specificity))

    # Compute posterior
    likelihood = (sensitivity * prior) + ((1 - specificity) * (1 - prior))
    if likelihood == 0:
        return 0.0
    return (sensitivity * prior) / likelihood


def load_data(filepath, strict=False, save_results=False, save_path=None):
    """
    Load CSV, compute posterior probabilities, handle invalid data.
    """
    df = pd.read_csv(filepath)

    expected_cols = {'prior','sensitivity','specificity'}
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {expected_cols}, found {df.columns.tolist()}")

    # Convert to numeric, invalid strings become NaN
    df[["prior","sensitivity","specificity"]] = df[["prior","sensitivity","specificity"]].apply(pd.to_numeric, errors='coerce')
    # Clip values to [0,1]
    df[["prior","sensitivity","specificity"]] = df[["prior","sensitivity","specificity"]].clip(0,1)

    # Identify invalid rows
    nan_mask = df[["prior","sensitivity","specificity"]].isna().any(axis=1)

    if strict:
        if nan_mask.any():
            bad_rows = df[nan_mask]
            raise ValueError(f"Invalid rows found:\n{bad_rows}")
        df_valid = df
    else:
        dropped_count = nan_mask.sum()
        if dropped_count > 0:
            print(f"Warning: Dropped {dropped_count} invalid row(s) due to non-numeric values.")
        df_valid = df[~nan_mask]

    # Vectorized posterior calculation
    df_valid['posterior'] = (df_valid['sensitivity'] * df_valid['prior']) / (
        (df_valid['sensitivity'] * df_valid['prior']) + ((1 - df_valid['specificity']) * (1 - df_valid['prior']))
    )

    # Optionally save results
    if save_results:
        if save_path is None:
            raise ValueError("save_path must be provided if save_results=True")
        df_valid.to_csv(save_path, index=False)

    return df_valid.to_dict(orient='records')


def display_results(results):
    """
    Nicely print a list of posterior probabilities.
    """
    for row in results:
        print(f"Prior: {row['prior']}, Sensitivity: {row['sensitivity']}, "
              f"Specificity: {row['specificity']}, Posterior: {row['posterior']:.4f}")


# Run as script
if __name__ == "__main__":
    data_file = 'data/hospital_data.csv'
    try:
        results = load_data(data_file)
        display_results(results)
    except Exception as e:
        print(f"Error: {e}")
