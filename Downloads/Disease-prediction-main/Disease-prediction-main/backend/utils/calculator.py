import csv

def bayesian_survival(prevalence, sensitivity, false_positive):
    """
    Calculate posterior probability using Bayes' Theorem.
    P(Disease | Positive) = (Sensitivity * Prevalence) /
                            [(Sensitivity * Prevalence) + (FalsePositive * (1 - Prevalence))]
    """
    p_pos = (sensitivity * prevalence) + (false_positive * (1 - prevalence))
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

if __name__ == "__main__":
    data_file = 'C:\\Users\\Vansh\\Desktop\\October\\Projects\\disease_refactor\\hospital_data.csv'
    results = load_data(data_file)
    display_results(results)
