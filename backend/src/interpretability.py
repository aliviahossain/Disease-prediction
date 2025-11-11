import shap
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from backend.src.multi_disease_pipeline import load_model

def shap_explain(disease, input_data, background_data):
    """Generate SHAP explanations for the given model."""
    model = load_model(disease)
    explainer = shap.Explainer(model, background_data)
    shap_values = explainer(input_data)

    st.subheader("Global Feature Importance")
    shap.summary_plot(shap_values, background_data, show=False)
    st.pyplot(plt.gcf())
    plt.clf()

    st.subheader("Local Explanation (For This Prediction)")
    shap.waterfall_plot(shap_values[0], show=False)
    st.pyplot(plt.gcf())
