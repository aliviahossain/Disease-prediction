# Data Privacy and Hospital Data Guidelines

## Overview
This application uses hospital statistical data for disease prediction analysis. To protect patient privacy and comply with healthcare regulations, sensitive data files must be handled carefully.

## Sensitive Files

The following files contain sensitive healthcare data and should NEVER be committed to version control:
- `hospital_data.csv` - Hospital prevalence, sensitivity, and specificity statistics
- `patient_data*.csv` - Any patient-specific or demographic data
- `*.health_data.csv` - Any healthcare-related data files
- `healthcare_*.csv` - Healthcare statistics files
- Database files (`.db`, `.sqlite`, `.sqlite3`)
- Application data files (`prediction_history.json`, `user_data.json`, etc.)

## Using Hospital Data Locally

### 1. Obtain Data
Contact the hospital data administrator or your healthcare partner to obtain the hospital_data.csv file with appropriate privacy review and agreements.

### 2. Setup Local File
```bash
# Copy the sensitive data to your local environment
cp hospital_data.csv .local/  # Store in local, untracked directory

# Or place it directly in the project root (will be ignored by git)
# Do NOT commit this file
```

### 3. Environment Configuration
Ensure your `.env` file is also in `.gitignore` (it should be):
```bash
# .env file should never be committed
# Set DATA_PATH environment variable if using non-default location
export DATA_PATH=./hospital_data.csv
```

### 4. Verify File is Ignored
```bash
# Confirm git ignores the hospital data
git check-ignore -v hospital_data.csv
# Output: hospital_data.csv     .gitignore:207

# Verify the file won't be committed
git status
# hospital_data.csv should NOT appear in "Untracked files"
```

## Using the Example File

The `hospital_data.example.csv` file shows the expected CSV format without actual data:

```csv
disease,prior_probability,sensitivity,specificity
Heart Disease,0.0000,0.0000,0.0000
Diabetes,0.0000,0.0000,0.0000
Breast Cancer,0.0000,0.0000,0.0000
```

Replace with actual prevalence, sensitivity, and specificity values from your hospital data.

## Privacy and Compliance

- **HIPAA Compliance**: In the US, ensure hospital data complies with HIPAA regulations
- **GDPR Compliance**: For EU data, ensure compliance with GDPR requirements
- **Data Anonymization**: All patient-level data must be anonymized or aggregated
- **Access Control**: Restrict access to hospital data to authorized personnel only
- **Audit Trail**: Log who accesses sensitive data and when

## Docker and Production Deployments

When deploying to production or Docker:
1. Mount hospital data as a secret/volume, do not bake it into the image
2. Use environment variables to reference the data file path
3. Ensure the data file has restricted file permissions (600 or 640)
4. Never include hospital data in Docker images or public repositories

## Verification

To verify sensitive data is not in git history:
```bash
# Search for previously committed hospital data
git log -p --all -- hospital_data.csv | head -20

# If found, the data was previously committed and should be removed from history
# This requires a git history rewrite (git filter-branch or similar)
```

## Questions?

If you have questions about data handling or privacy, please contact the project maintainers at [email].
