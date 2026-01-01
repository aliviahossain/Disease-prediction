import streamlit as st
import pandas as pd
import sys
import os

# Add the current directory to sys.path to ensure we can import backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.models.ml_model import ml_model

st.set_page_config(page_title="🩺 Multi-Disease Prediction Dashboard", layout="wide")

st.title("🩺 Multi-Disease Prediction System")
st.markdown("### Interactive Dashboard for Disease Prediction & Analysis")

# Sidebar for navigation
st.sidebar.header("Navigation")
app_mode = st.sidebar.selectbox("Choose Mode", ["Prediction", "Model Insights"])

if app_mode == "Prediction":
    st.subheader("Patient Symptom Analysis")
    
    # Get available diseases
    diseases = ml_model.get_available_diseases()
    selected_disease = st.selectbox("Select Disease to Analyze:", diseases, format_func=lambda x: x.replace('_', ' ').title())
    
    if selected_disease:
        st.divider()
        st.write(f"#### Select Symptoms for {selected_disease.replace('_', ' ').title()}")
        
        # Get symptoms for the selected disease
        symptoms_map = ml_model.get_disease_symptoms(selected_disease)
        
        # Create checkboxes for symptoms
        selected_symptoms = []
        cols = st.columns(3)
        
        for i, (key, label) in enumerate(symptoms_map.items()):
            with cols[i % 3]:
                if st.checkbox(label, key=key):
                    selected_symptoms.append(key)
        
        st.divider()
        
        if st.button("Analyze Symptoms", type="primary"):
            if not selected_symptoms:
                st.warning("Please select at least one symptom.")
            else:
                try:
                    # Get prediction
                    result = ml_model.predict_disease_probability(selected_disease, selected_symptoms)
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Probability", f"{result['raw_probability']*100:.1f}%")
                    
                    with col2:
                        st.metric("Confidence Score", f"{result['confidence_score']*100:.1f}%")
                        
                    with col3:
                        st.metric("Symptoms Matched", f"{result['symptoms_matched']} / {result['total_symptoms']}")
                    
                    # Risk Assessment
                    prob = result['raw_probability'] * 100
                    if prob < 30:
                        st.success("✅ Low Risk: Symptoms do not strongly indicate this disease.")
                    elif prob < 60:
                        st.warning("⚠️ Moderate Risk: Consider consulting a doctor for further evaluation.")
                    else:
                        st.error("🚨 High Risk: Immediate medical attention is recommended.")
                        
                except Exception as e:
                    st.error(f"An error occurred during prediction: {str(e)}")

elif app_mode == "Model Insights":
    st.subheader("Model Interpretability")
    st.write("Visualize which symptoms contribute most to detecting a specific disease.")
    
    diseases = ml_model.get_available_diseases()
    disease_for_insight = st.selectbox("Select Disease:", diseases, format_func=lambda x: x.replace('_', ' ').title())
    
    if disease_for_insight:
        # Get symptom importance using the model's built-in method
        importance = ml_model.get_symptom_importance(disease_for_insight)
        
        # Create a DataFrame for plotting
        df_importance = pd.DataFrame(list(importance.items()), columns=['Symptom', 'Importance'])
        
        # Display as a bar chart
        st.bar_chart(df_importance.set_index('Symptom'))
        
        st.write("Reviewing these weights helps understand which symptoms the model considers critical for diagnosis.")
