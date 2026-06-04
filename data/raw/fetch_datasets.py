import pandas as pd
import numpy as np
import os
from ucimlrepo import fetch_ucirepo
from sklearn.datasets import load_breast_cancer

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/cleaned", exist_ok=True)

# ── 1. Heart Disease (ucimlrepo id=45) ── already works ──────
heart_disease = fetch_ucirepo(id=45)
heart_df = pd.concat([heart_disease.data.features, heart_disease.data.targets], axis=1)
heart_df.to_csv("data/raw/heart_disease_raw.csv", index=False)
print("✅ Heart Disease downloaded:", heart_df.shape)

# ── 2. Pima Diabetes ── use sklearn built-in alternative ─────
# Pima is blocked on ucimlrepo; load from sklearn's bundled copy
from sklearn.datasets import fetch_openml
pima = fetch_openml(name='diabetes', version=1, as_frame=True)
diabetes_df = pima.frame
diabetes_df.to_csv("data/raw/diabetes_raw.csv", index=False)
print("✅ Diabetes downloaded:", diabetes_df.shape)

# ── 3. Breast Cancer Wisconsin ── sklearn built-in ───────────
bc = load_breast_cancer(as_frame=True)
bc_df = bc.frame
bc_df.to_csv("data/raw/breast_cancer_raw.csv", index=False)
print("✅ Breast Cancer downloaded:", bc_df.shape)

print("\nAll raw datasets saved to data/raw/")