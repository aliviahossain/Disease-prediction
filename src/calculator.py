import csv

def bayesian_survival(prior, sensitivity, specificity):
    """
    Calculate posterior probability using Bayes' Theorem.
    """
    likelihood = (sensitivity * prior) + ((1 - specificity) * (1 - prior))
    posterior = (sensitivity * prior) / likelihood
    return posterior

def load_data(filepath):
    """
    Load data from CSV and calculate posterior probabilities.
    """
    results = []
    with open(filepath, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            prior = float(row['Prevalence'])
            sensitivity = float(row['Sensitivity'])
            false_positive = float(row['FalsePositive'])
            specificity = 1 - false_positive  # Convert false positive rate to specificity
            posterior = bayesian_survival(prior, sensitivity, specificity)
            row['posterior'] = posterior
            results.append(row)
    return results

def display_results(results):
    """
    Display the posterior probabilities.
    """
    for result in results:
        print(f"Disease: {result['Disease']}")
        print(f"  Prevalence: {result['Prevalence']}, Sensitivity: {result['Sensitivity']}, "
              f"False Positive: {result['FalsePositive']}, Posterior: {result['posterior']:.4f}")
        print()

if __name__ == "__main__":
    data_file = '../hospital_data.csv'  # Updated path to match actual file location
    results = load_data(data_file)
    display_results(results)
