import streamlit as st
import pandas as pd
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import ML model
from backend.models.ml_model import ml_model

# Import disease descriptions
from backend.data.disease_info import DISEASE_INFO

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="🩺 Multi-Disease Prediction Dashboard",
    layout="wide"
)

# =========================
# TITLE
# =========================
st.title("🩺 Multi-Disease Prediction System")
st.markdown(
    "### Interactive Dashboard for Disease Prediction & Analysis"
)

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Navigation")

app_mode = st.sidebar.selectbox(
    "Choose Mode",
    ["Prediction", "Model Insights"]
)

# =========================
# PREDICTION MODE
# =========================
if app_mode == "Prediction":

    st.subheader("Patient Symptom Analysis")

    # Get available diseases
    diseases = ml_model.get_available_diseases()

    # Disease selection
    selected_disease = st.selectbox(
        "Select Disease to Analyze:",
        diseases,
        format_func=lambda x: x.replace('_', ' ').title()
    )

    # Disease info
    if selected_disease in DISEASE_INFO:
        st.info(DISEASE_INFO[selected_disease])

    st.divider()

    # =========================
    # SYMPTOM SELECTION
    # =========================
    st.write(
        f"#### Select Symptoms for "
        f"{selected_disease.replace('_', ' ').title()}"
    )

    symptoms_map = ml_model.get_disease_symptoms(
        selected_disease
    )

    selected_symptoms = []

    cols = st.columns(3)

    for i, (key, label) in enumerate(
        symptoms_map.items()
    ):

        with cols[i % 3]:

            if st.checkbox(label, key=key):
                selected_symptoms.append(key)

    st.divider()

    # =========================
    # ANALYZE BUTTON
    # =========================
    if st.button(
        "Analyze Symptoms",
        type="primary"
    ):

        if not selected_symptoms:

            st.warning(
                "Please select at least one symptom."
            )

        else:

            try:

                # =========================
                # PREDICTION
                # =========================
                result = ml_model.predict_disease_probability(
                    selected_disease,
                    selected_symptoms
                )

                # =========================
                # METRICS
                # =========================
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Probability",
                        f"{result['raw_probability'] * 100:.1f}%"
                    )

                with col2:
                    st.metric(
                        "Confidence Score",
                        f"{result['confidence_score'] * 100:.1f}%"
                    )

                with col3:
                    st.metric(
                        "Symptoms Matched",
                        f"{result['symptoms_matched']} / "
                        f"{result['total_symptoms']}"
                    )

                # =========================
                # PROGRESS BAR
                # =========================
                st.write("### Risk Probability")

                st.progress(
                    result['raw_probability']
                )

                st.divider()

                # =========================
                # RISK ASSESSMENT
                # =========================
                prob = (
                    result['raw_probability']
                    * 100
                )

                if prob < 30:

                    st.success(
                        "✅ Low Risk: Symptoms do not strongly "
                        "indicate this disease."
                    )

                elif prob < 60:

                    st.warning(
                        "⚠️ Moderate Risk: Consider consulting "
                        "a doctor for further evaluation."
                    )

                else:

                    st.error(
                        "🚨 High Risk: Immediate medical "
                        "attention is recommended."
                    )

                # =========================
                # BAYES THEOREM SECTION
                # =========================
                st.divider()

                st.subheader(
                    " Bayesian Probability Concept"
                )

                st.write("""
                This prediction system uses
                probabilistic reasoning inspired by
                Bayes' Theorem to estimate disease
                likelihood based on symptoms.
                """)

                # Formula
                st.latex(
                    r"P(D \mid S)=\frac{P(S \mid D)\cdot P(D)}{P(S)}"
                )

                st.caption(
                    """
                    D = Disease
                    | S = Symptoms
                    """
                )

                # Explanation Cards
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.info("""
                    **P(D)**

                    Prior probability
                    of disease
                    """)

                with col2:
                    st.info("""
                    **P(S|D)**

                    Probability of symptoms
                    given disease
                    """)

                with col3:
                    st.info("""
                    **P(D|S)**

                    Updated disease
                    probability
                    """)

            except Exception as e:

                st.error(
                    f"An error occurred during prediction: "
                    f"{str(e)}"
                )

# =========================
# MODEL INSIGHTS MODE
# =========================
elif app_mode == "Model Insights":

    st.subheader("Model Interpretability")

    st.write(
        "Visualize which symptoms contribute most "
        "to detecting a specific disease."
    )

    diseases = ml_model.get_available_diseases()

    disease_for_insight = st.selectbox(
        "Select Disease:",
        diseases,
        format_func=lambda x: x.replace('_', ' ').title()
    )

    if disease_for_insight:

        # Get symptom importance
        importance = ml_model.get_symptom_importance(
            disease_for_insight
        )

        # Create DataFrame
        df_importance = pd.DataFrame(
            list(importance.items()),
            columns=['Symptom', 'Importance']
        )

        # Display chart
        st.bar_chart(
            df_importance.set_index('Symptom')
        )

        st.write(
            "Reviewing these weights helps understand "
            "which symptoms the model considers critical "
            "for diagnosis."
        )