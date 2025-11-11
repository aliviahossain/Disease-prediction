import streamlit as st
import pandas as pd
from backend.src.multi_disease_pipeline import predict_disease
from backend.src.interpretability import shap_explain

st.set_page_config(page_title="🩺 Multi-Disease Prediction Dashboard", layout="wide")

st.title("🩺 Multi-Disease Prediction + Model Interpretability")

# Select the disease
disease = st.selectbox("Select Disease:", ["heart", "liver", "diabetes"])

st.write(f"### Enter Patient Data for {disease.capitalize()} Prediction")

n_features = st.number_input("Number of Input Features", min_value=1, max_value=20, value=8)
features = [st.number_input(f"Feature {i+1}", value=0.0) for i in range(n_features)]

if st.button("Predict"):
    result = predict_disease(disease, features)
    st.success(f"Prediction: {'Positive' if result['prediction'] == 1 else 'Negative'}")
    if result["confidence"]:
        st.info(f"Confidence: {result['confidence']*100:.2f}%")

    st.divider()
    st.header("🔍 Model Interpretability")
    st.write("Analyzing model reasoning using SHAP values...")
    background_data = pd.DataFrame([features] * 20)
    shap_explain(disease, pd.DataFrame([features]), background_data)
