import csv
import logging
from typing import List, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)


def bayesian_survival(prevalence: float, sensitivity: float, false_positive: float) -> float:
    """
    Calculate posterior probability using Bayes' Theorem.
    
    Formula:
        P(Disease | Positive) = (Sensitivity * Prevalence) /
                                [(Sensitivity * Prevalence) + (FalsePositive * (1 - Prevalence))]
    
    Args:
        prevalence: Prior probability of disease (0-1)
        sensitivity: True positive rate (0-1)
        false_positive: False positive rate (0-1)
    
    Returns:
        float: Posterior probability of disease given positive test
        
    Raises:
        ValueError: If inputs are not in valid range [0, 1]
        ZeroDivisionError: If denominator is zero
    """
    # Input validation
    for name, value in [
        ("prevalence", prevalence),
        ("sensitivity", sensitivity),
        ("false_positive", false_positive)
    ]:
        if not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number, got {type(value).__name__}")
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"{name} must be between 0 and 1, got {value}")
    
    # Calculate denominator
    denominator = (sensitivity * prevalence) + (false_positive * (1 - prevalence))
    
    if denominator == 0:
        logger.warning(
            f"Division by zero in bayesian_survival: "
            f"prevalence={prevalence}, sensitivity={sensitivity}, false_positive={false_positive}"
        )
        raise ZeroDivisionError(
            "Cannot calculate posterior probability: denominator is zero. "
            "This occurs when both (sensitivity * prevalence) and "
            "(false_positive * (1 - prevalence)) equal zero."
        )
    
    posterior = (sensitivity * prevalence) / denominator
    
    logger.debug(
        f"Bayesian calculation: prevalence={prevalence:.4f}, "
        f"sensitivity={sensitivity:.4f}, false_positive={false_positive:.4f}, "
        f"posterior={posterior:.4f}"
    )
    
    return posterior


def load_data(filepath: str) -> List[Dict[str, any]]:
    """
    Load hospital data from CSV and calculate posterior probabilities.
    
    Args:
        filepath: Path to the CSV file containing hospital data
        
    Returns:
        List[Dict]: List of dictionaries with disease data and calculated posteriors
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If CSV is missing required columns or has invalid data
        PermissionError: If file cannot be read due to permissions
    """
    # Validate file exists
    import os
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    if not os.access(filepath, os.R_OK):
        raise PermissionError(f"Cannot read file: {filepath}")
    
    results = []
    required_columns = {"Disease", "Prevalence", "Sensitivity", "FalsePositive"}
    
    try:
        with open(filepath, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            # Validate required columns exist
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no headers")
            
            missing_columns = required_columns - set(reader.fieldnames)
            if missing_columns:
                raise ValueError(
                    f"CSV missing required columns: {missing_columns}. "
                    f"Found columns: {reader.fieldnames}"
                )
            
            row_number = 1  # Start at 1 (header is row 0)
            for row in reader:
                row_number += 1
                
                try:
                    # Extract and validate data
                    disease = row.get("Disease", "").strip()
                    if not disease:
                        logger.warning(f"Row {row_number}: Empty disease name, skipping")
                        continue
                    
                    prevalence = float(row["Prevalence"])
                    sensitivity = float(row["Sensitivity"])
                    false_positive = float(row["FalsePositive"])
                    
                    # Calculate posterior
                    posterior = bayesian_survival(prevalence, sensitivity, false_positive)
                    
                    # Add to results
                    result = row.copy()
                    result["Posterior"] = round(posterior, 4)
                    results.append(result)
                    
                except ValueError as e:
                    logger.error(f"Row {row_number} ({disease if 'disease' in locals() else 'unknown'}): {str(e)}")
                    raise ValueError(f"Invalid data in row {row_number}: {str(e)}")
                except ZeroDivisionError as e:
                    logger.error(f"Row {row_number} ({disease}): {str(e)}")
                    raise ValueError(f"Calculation error in row {row_number} ({disease}): {str(e)}")
        
        logger.info(f"Successfully loaded {len(results)} records from {filepath}")
        return results
        
    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {str(e)}")


def display_results(results: List[Dict[str, any]]) -> None:
    """
    Display the posterior probabilities in a formatted manner.
    
    Args:
        results: List of dictionaries containing disease data and posteriors
    """
    if not results:
        print("No results to display")
        return
    
    print(f"\n{'='*80}")
    print(f"{'Disease Prediction Results':^80}")
    print(f"{'='*80}\n")
    
    for idx, result in enumerate(results, 1):
        try:
            disease = result.get("Disease", "Unknown")
            prevalence = float(result.get("Prevalence", 0))
            sensitivity = float(result.get("Sensitivity", 0))
            false_positive = float(result.get("FalsePositive", 0))
            posterior = float(result.get("Posterior", 0))
            specificity = 1 - false_positive
            
            print(f"{idx}. {disease}")
            print(f"   Prevalence (Prior):     {prevalence:.4f} ({prevalence*100:.2f}%)")
            print(f"   Sensitivity:            {sensitivity:.4f} ({sensitivity*100:.2f}%)")
            print(f"   Specificity:            {specificity:.4f} ({specificity*100:.2f}%)")
            print(f"   False Positive Rate:    {false_positive:.4f} ({false_positive*100:.2f}%)")
            print(f"   Posterior Probability:  {posterior:.4f} ({posterior*100:.2f}%)")
            print()
            
        except (ValueError, KeyError) as e:
            logger.warning(f"Error displaying result {idx}: {str(e)}")
            print(f"{idx}. Error displaying result: {str(e)}\n")


if __name__ == "__main__":
    # Example usage with relative path
    import os
    
    # Try to find the data file
    possible_paths = [
        'hospital_data.csv',
        '../hospital_data.csv',
        '../../hospital_data.csv',
        '../../../hospital_data.csv'
    ]
    
    data_file = None
    for path in possible_paths:
        if os.path.exists(path):
            data_file = path
            break
    
    if not data_file:
        print("Error: Could not find hospital_data.csv")
        print("Searched in:", possible_paths)
        exit(1)
    
    try:
        print(f"Loading data from: {os.path.abspath(data_file)}\n")
        results = load_data(data_file)
        display_results(results)
        
    except Exception as e:
        logger.exception("Error processing data")
        print(f"\nError: {str(e)}")
        exit(1)
