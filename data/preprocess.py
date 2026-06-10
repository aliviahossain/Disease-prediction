import pandas as pd
import numpy as np

def process_heart_disease(raw_path):
    df = pd.read_csv(raw_path)
    
    # 'num' column: 0 = no disease, 1-4 = disease present
    df['target'] = (df['num'] > 0).astype(int)
    
    prevalence = df['target'].mean()
    positive_cases = df[df['target'] == 1]
    negative_cases = df[df['target'] == 0]
    
    threshold = df['thalach'].median()
    sensitivity = (positive_cases['thalach'] < threshold).mean()
    specificity = (negative_cases['thalach'] >= threshold).mean()
    
    return {
        "disease": "Heart Disease",
        "prior_probability": round(prevalence, 4),
        "sensitivity": round(sensitivity, 4),
        "specificity": round(specificity, 4)
    }

def process_diabetes(raw_path):
    df = pd.read_csv(raw_path)
    
    # Replace 0s in medical columns with NaN
    cols_with_zeros = ['plas', 'pres', 'skin', 'insu', 'mass']
    df[cols_with_zeros] = df[cols_with_zeros].replace(0, np.nan)
    df.dropna(inplace=True)
    
    # Convert string class to numeric: tested_positive=1, tested_negative=0
    df['target'] = (df['class'] == 'tested_positive').astype(int)
    
    prevalence = df['target'].mean()
    positive = df[df['target'] == 1]
    negative = df[df['target'] == 0]
    
    threshold = df['plas'].median()
    sensitivity = (positive['plas'] >= threshold).mean()
    specificity = (negative['plas'] < threshold).mean()
    
    return {
        "disease": "Diabetes",
        "prior_probability": round(prevalence, 4),
        "sensitivity": round(sensitivity, 4),
        "specificity": round(specificity, 4)
    }

def process_breast_cancer(raw_path):
    df = pd.read_csv(raw_path)
    
    # 'target' column: 1 = malignant, 0 = benign
    prevalence = df['target'].mean()
    positive = df[df['target'] == 1]
    negative = df[df['target'] == 0]
    
    # Use 'mean radius' as the key diagnostic feature
    threshold = df['mean radius'].median()
    sensitivity = (positive['mean radius'] >= threshold).mean()
    specificity = (negative['mean radius'] < threshold).mean()
    
    return {
        "disease": "Breast Cancer",
        "prior_probability": round(prevalence, 4),
        "sensitivity": round(sensitivity, 4),
        "specificity": round(specificity, 4)
    }

def build_hospital_data():
    rows = [
        process_heart_disease("data/raw/heart_disease_raw.csv"),
        process_diabetes("data/raw/diabetes_raw.csv"),
        process_breast_cancer("data/raw/breast_cancer_raw.csv"),
    ]
    df = pd.DataFrame(rows)
    df.to_csv("data/cleaned/hospital_data_cleaned.csv", index=False)
    df.to_csv("hospital_data.csv", index=False)
    print("Done! hospital_data.csv updated.")

if __name__ == "__main__":
    build_hospital_data()