import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sys
import os
from datetime import datetime
import plotly.express as px
import re

def highlight_text(text, query):
    if not query or not query.strip():
        return text
    query = query.strip()
    pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE)
    return pattern.sub(
        r"<mark style='background-color:#fffa65; color:black; padding:0 2px; border-radius:3px;'>\1</mark>",
        text
    )

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import ML model
from backend.models.ml_model import ml_model

# Import disease descriptions
from backend.data.disease_info import DISEASE_INFO

# Import history manager
from backend.utils.history_manager import (
    load_history,
    save_history
)

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

    # Get symptoms
    symptoms_map = ml_model.get_disease_symptoms(selected_disease)
    # 🔍 SEARCH BAR
    search_query = st.text_input(
        "🔍 Search Symptoms",
        placeholder="Type to filter symptoms...",
        key="symptom_search"
    )

    # 🔎 SUGGESTIONS (NEW)
    if search_query:
        suggestions = [
            label for label in symptoms_map.values()
            if search_query.lower() in label.lower()
        ][:5]

        if suggestions:
            st.write("### Suggestions:")
            for s in suggestions:
                components.html(
                    f"<div>👉 {highlight_text(s, search_query)}</div>",
                    height=30,
                    scrolling=False
                )

    # 🔎 Apply filtering
    if search_query:
        filtered_symptoms = {
            key: label
            for key, label in symptoms_map.items()
            if search_query.lower() in label.lower()
        }
    else:
        filtered_symptoms = symptoms_map

    # ⚠️ No results case
    if search_query and not filtered_symptoms:
        st.warning("No matching symptoms found. Try a different keyword.")

    selected_symptoms = []
    cols = st.columns(2)

    # ✅ Display filtered checkboxes
    for i, (key, label) in enumerate(filtered_symptoms.items()):
        with cols[i % 2]:

            display_label = highlight_text(label, search_query)

            col_checkbox, col_text = st.columns([1, 5])

            with col_checkbox:
                if st.checkbox("", key=key):
                    selected_symptoms.append(key)

            with col_text:
                components.html(
                    display_label,
                    height=30,
                    scrolling=False
                )
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
                # SAVE PREDICTION HISTORY
                # =========================
                probability = round(
                    result['raw_probability'] * 100,
                    1
                )

                if probability < 30:
                    risk_level = "Low"

                elif probability < 60:
                    risk_level = "Moderate"

                else:
                    risk_level = "High"

                history_entry = {
                    "Disease": selected_disease.replace('_', ' ').title(),
                    "Probability": probability,
                    "Risk": risk_level,
                    "Symptoms": ", ".join(selected_symptoms),
                    "Timestamp": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                }

                # Save prediction history
                save_history(history_entry)

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
                    "Bayesian Probability Concept"
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

                # =========================
                # PREDICTION HISTORY
                # =========================
                st.divider()

                st.subheader(
                    "📜 Prediction History Timeline"
                )

                # Load prediction history
                history_data = load_history()

                if history_data:

                    df_history = pd.DataFrame(history_data)

                    # Latest predictions first
                    df_history = df_history.iloc[::-1]

                    # Display table
                    st.dataframe(
                        df_history,
                        use_container_width=True
                    )

                    st.divider()

                    # =========================
                    # ANALYTICS CHART
                    # =========================
                    st.subheader(
                        "📈 Probability Trend Analytics"
                    )

                    fig = px.line(
                        df_history,
                        x="Timestamp",
                        y="Probability",
                        color="Disease",
                        markers=True,
                        title="Disease Probability Over Time"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                    # =========================
                    # RISK DISTRIBUTION
                    # =========================
                    st.subheader(
                        "⚠️ Risk Distribution"
                    )

                    risk_counts = (
                        df_history["Risk"]
                        .value_counts()
                    )

                    st.bar_chart(risk_counts)

                else:

                    st.info(
                        "No prediction history available yet."
                    )

            except Exception as e:

                st.error(
                    f"An error occurred during prediction: "
                    f"{str(e)}"
                )

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

        importance = ml_model.get_symptom_importance(
            disease_for_insight
        )

        df_importance = pd.DataFrame(
            list(importance.items()),
            columns=['Symptom', 'Importance']
        )

        st.bar_chart(
            df_importance.set_index('Symptom')
        )

        st.write(
            "Reviewing these weights helps understand "
            "which symptoms the model considers critical "
            "for diagnosis."
        )