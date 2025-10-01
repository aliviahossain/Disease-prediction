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
            prior = float(row['prior'])
            sensitivity = float(row['sensitivity'])
            specificity = float(row['specificity'])
            posterior = bayesian_survival(prior, sensitivity, specificity)
            row['posterior'] = posterior
            results.append(row)
    return results

def display_results(results):
    """
    Display the posterior probabilities.
    """
    for result in results:
        print(f"Prior: {result['prior']}, Sensitivity: {result['sensitivity']}, "
              f"Specificity: {result['specificity']}, Posterior: {result['posterior']:.4f}")

if __name__ == "__main__":
    data_file = 'data/hospital_data.csv'
    results = load_data(data_file)
    display_results(results)
