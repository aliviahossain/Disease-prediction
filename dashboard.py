import os
import sys
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
import re


def highlight_text(text: str, query: str) -> str:
    if not query or not query.strip():
        return text
    query = query.strip()
    pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE)
    return pattern.sub(
        r"<mark style='background-color:#fffa65; color:black; padding:0 2px; border-radius:3px;'>\1</mark>",
        text,
    )


# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import disease descriptions
from backend.data.disease_info import DISEASE_INFO

# Import ML model
from backend.models.ml_model import ml_model

# Import history manager
from backend.utils.history_manager import clear_history, load_history, save_history

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="🩺 Multi-Disease Prediction Dashboard", layout="wide")

# =========================
# TITLE
# =========================
st.title("🩺 Multi-Disease Prediction System")

st.markdown("### Interactive Dashboard for Disease Prediction & Analysis")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Navigation")

app_mode = st.sidebar.selectbox("Choose Mode", ["Prediction", "Model Insights"])

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
        format_func=lambda x: x.replace("_", " ").title(),
    )

    # Disease info
    if selected_disease in DISEASE_INFO:
        st.info(DISEASE_INFO[selected_disease])

    st.divider()

    # =========================
    # SYMPTOM SELECTION
    # =========================
    st.write(f"#### Select Symptoms for {selected_disease.replace('_', ' ').title()}")

    symptoms_map = ml_model.get_disease_symptoms(selected_disease)

    # 🔍 SEARCH BAR
    search_query = st.text_input(
        "🔍 Search Symptoms",
        placeholder="Type to filter symptoms...",
        key="symptom_search",
    )

    # 🔎 SUGGESTIONS
    if search_query:
        suggestions = [
            label
            for label in symptoms_map.values()
            if search_query.lower() in label.lower()
        ][:5]

        if suggestions:
            st.write("### Suggestions:")
            for s in suggestions:
                st.markdown(
                    f"<div>👉 {highlight_text(s, search_query)}</div>",
                    unsafe_allow_html=True,
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

    for i, (key, label) in enumerate(filtered_symptoms.items()):
        with cols[i % 2]:
            display_label = highlight_text(label, search_query)
            col_checkbox, col_text = st.columns([1, 10])
            with col_checkbox:
                if st.checkbox("", key=key):
                    selected_symptoms.append(key)
            with col_text:
                st.markdown(display_label, unsafe_allow_html=True)

    st.divider()

    # =========================
    # ANALYZE BUTTON & LOGIC
    # =========================
    if st.button("Analyze Symptoms", type="primary"):
        if not selected_symptoms:
            st.warning("Please select at least one symptom.")
        else:
            try:
                result = ml_model.predict_disease_probability(
                    selected_disease, selected_symptoms
                )
                probability = round(result["raw_probability"] * 100, 1)
                if probability < 30:
                    risk_level = "Low"
                elif probability < 60:
                    risk_level = "Moderate"
                else:
                    risk_level = "High"

                history_entry = {
                    "Disease": selected_disease.replace("_", " ").title(),
                    "Probability": probability,
                    "Risk": risk_level,
                    "Symptoms": ", ".join(selected_symptoms),
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                save_history(history_entry)
                st.session_state["active_result"] = result
            except Exception as e:
                st.error(f"An error occurred during prediction: {str(e)}")

    # Display Active Prediction Results if available
    if st.session_state.get("active_result"):
        result = st.session_state["active_result"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Probability", f"{result['raw_probability'] * 100:.1f}%")
        with col2:
            st.metric("Confidence Score", f"{result['confidence_score'] * 100:.1f}%")
        with col3:
            st.metric("Symptoms Matched", f"{result['symptoms_matched']} / {result['total_symptoms']}")

        st.write("### Risk Probability")
        st.progress(result["raw_probability"])
        st.divider()

        prob = result["raw_probability"] * 100
        if prob < 30:
            st.success("✅ Low Risk: Symptoms do not strongly indicate this disease.")
        elif prob < 60:
            st.warning("⚠️ Moderate Risk: Consider consulting a doctor for further evaluation.")
        else:
            st.error("🚨 High Risk: Immediate medical attention is recommended.")

        st.divider()
        st.subheader("Bayesian Probability Concept")
        st.write("This prediction system uses probabilistic reasoning inspired by Bayes' Theorem to estimate disease likelihood based on symptoms.")
        st.latex(r"P(D \mid S)=\frac{P(S \mid D)\cdot P(D)}{P(S)}")
        st.caption("D = Disease | S = Symptoms")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**P(D)**\n\nPrior probability of disease")
        with col2:
            st.info("**P(S|D)**\n\nProbability of symptoms given disease")
        with col3:
            st.info("**P(D|S)**\n\nUpdated disease probability")

    # =========================
    # PREDICTION HISTORY TIMELINE
    # =========================
    st.divider()
    col_hist_title, col_hist_clear = st.columns([3, 1])
    with col_hist_title:
        st.subheader("📜 Prediction History Timeline")

    history_data = load_history()

    if history_data:
        with col_hist_clear:
            if st.button("🗑️ Clear History", key="btn_clear_history"):
                st.session_state["show_clear_confirm"] = True

        if st.session_state.get("show_clear_confirm", False):
            st.warning(
                "⚠️ **Are you sure you want to clear all prediction history?** This action cannot be undone."
            )
            col_confirm_yes, col_confirm_no, _ = st.columns([2, 2, 6])
            with col_confirm_yes:
                if st.button("Yes, Clear All", key="btn_clear_yes", type="primary"):
                    clear_history()
                    st.session_state["show_clear_confirm"] = False
                    if "active_result" in st.session_state:
                        del st.session_state["active_result"]
                    st.success("Prediction history cleared successfully!")
                    st.rerun()
            with col_confirm_no:
                if st.button("Cancel", key="btn_clear_no"):
                    st.session_state["show_clear_confirm"] = False
                    st.rerun()

        df_history = pd.DataFrame(history_data)
        df_history = df_history.iloc[::-1]
        st.dataframe(df_history, use_container_width=True)

        st.divider()
        st.subheader("📈 Probability Trend Analytics")
        fig = px.line(
            df_history,
            x="Timestamp",
            y="Probability",
            color="Disease",
            markers=True,
            title="Disease Probability Over Time",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("⚠️ Risk Distribution")
        risk_counts = df_history["Risk"].value_counts()
        st.bar_chart(risk_counts)
    else:
        st.info("No prediction history available yet.")


elif app_mode == "Model Insights":
    st.subheader("Model Interpretability")

    st.write(
        "Visualize which symptoms contribute most to detecting a specific disease."
    )

    diseases = ml_model.get_available_diseases()

    disease_for_insight = st.selectbox(
        "Select Disease:", diseases, format_func=lambda x: x.replace("_", " ").title()
    )

    if disease_for_insight:
        # Get symptom importance
        importance = ml_model.get_symptom_importance(disease_for_insight)

        df_importance = pd.DataFrame(
            list(importance.items()), columns=["Symptom", "Importance"]
        )

        # Display chart
        st.bar_chart(df_importance.set_index("Symptom"))

        st.write(
            "Reviewing these weights helps understand "
            "which symptoms the model considers critical "
            "for diagnosis."
        )
