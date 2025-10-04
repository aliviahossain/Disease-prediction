import pandas as pd

def bayesian_survival(prior, sensitivity, specificity):

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


def read_data(filepath):

    df = pd.read_csv(filepath)
    expected_cols = {'prior', 'sensitivity', 'specificity'}
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {expected_cols}, found {df.columns.tolist()}")
    return df


def clean_data(df, strict=False):

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

    df = df.copy()
    df['posterior'] = (
        df['sensitivity'] * df['prior']
        / (
            (df['sensitivity'] * df['prior'])
            + ((1 - df['specificity']) * (1 - df['prior']))
        )
    ).fillna(0.0)
    return df


def save_results(df, save_path):

    df.to_csv(save_path, index=False)


def load_data(filepath, strict=False, save_results_flag=False, save_path=None):

    df = read_data(filepath)
    df = clean_data(df, strict=strict)
    df = add_posterior_column(df)

    if save_results_flag:
        if save_path is None:
            raise ValueError("save_path must be provided if save_results_flag=True")
        save_results(df, save_path)

    return df.to_dict(orient='records')


def display_results(results):

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
