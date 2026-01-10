"""
Gemini API helper for generating recommendations based on disease probability results.
"""

import os
import google.generativeai as genai
from typing import Optional

def configure_gemini():
    """Configure Gemini API with the API key from environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)


def generate_recommendations(disease_name: Optional[str], 
                            prior_probability: float, 
                            posterior_probability: float,
                            test_result: str = "positive",
                            language: str = "english") -> dict:
    """
    Generate AI-powered recommendations using Gemini API based on disease probability results.
    
    Args:
        disease_name: Name of the disease (optional, can be None for custom input)
        prior_probability: Prior probability of disease (before test)
        posterior_probability: Posterior probability of disease (after test)
        test_result: The test result ("positive" or "negative")
        language: Language for the response (english, hindi, gujarati, tamil)
    
    Returns:
        dict: Contains 'success', 'recommendations', and optional 'error' keys
    """
    try:
        configure_gemini()
        
        # Create the model - use the latest available flash model
        # Try newer models first, fall back to older ones if needed
        model_names = [ 'gemini-2.5-flash', 'gemini-2.5-pro']
        model = None
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                break
            except:
                continue
        
        if model is None:
            model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Construct the prompt
        disease_context = f"the disease '{disease_name}'" if disease_name else "a disease"
        
        # Language mapping for prompt instructions
        language_instructions = {
            "english": "Respond in English.",
            "hindi": "Respond in Hindi (हिंदी में जवाब दें). Use Devanagari script.",
            "gujarati": "Respond in Gujarati (ગુજરાતીમાં જવાબ આપો). Use Gujarati script.",
            "tamil": "Respond in Tamil (தமிழில் பதிலளிக்கவும்). Use Tamil script."
        }
        
        language_instruction = language_instructions.get(language.lower(), language_instructions["english"])
        
        prompt = f"""
You are a medical informatics assistant helping to interpret diagnostic test results.

IMPORTANT: {language_instruction}

Context:
- Disease/Condition: {disease_context}
- Test Result: {test_result.upper()}
- Prior Probability (before test): {prior_probability * 100:.2f}%
- Posterior Probability (after test): {posterior_probability * 100:.2f}%

Based on these Bayesian probability results, provide clear, actionable recommendations for what to do next. 
Structure your response in the following format:

**Interpretation:**
(Brief explanation of what these numbers mean in plain language)

**Recommended Next Steps:**
(2-4 specific, practical recommendations such as: further testing, consultation with specialists, lifestyle changes, monitoring, etc.)

**Important Notes:**
(Any critical considerations or disclaimers)

Keep your response concise (under 200 words), professional, educational, and emphasize that this is a probabilistic tool, not a definitive diagnosis. The recommendations should be general guidance that would apply to most cases.
"""
        
        # Generate response
        response = model.generate_content(prompt)
        
        return {
            "success": True,
            "recommendations": response.text,
            "prior_probability": prior_probability,
            "posterior_probability": posterior_probability
        }
        
    except ValueError as ve:
        return {
            "success": False,
            "error": str(ve),
            "recommendations": "API key not configured. Please set GEMINI_API_KEY environment variable."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "recommendations": "Unable to generate recommendations at this time. Please try again later."
        }


def generate_chat_response(message: str, history: list = None) -> dict:
    """
    Generate a chat response using Gemini API, restricted to medical/health domain.
    
    Args:
        message: The user's query
        history: Optional list of previous chat messages for context
    
    Returns:
        dict: Contains 'success', 'response', and optional 'error' keys
    """
    try:
        configure_gemini()
        
        # Create the model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # System instruction to restrict domain
        system_instruction = """
        You are a helpful AI assistant for a Disease Prediction Application.
        
        YOUR ROLE:
        - Helper users understand disease predictions.
        - Answer general health and medical questions.
        - Explain how to use the application (symptom checker, calculator, etc.).
        
        STRICT RULES:
        1. ONLY answer questions related to health, medicine, diseases, symptoms, treatments, and this application.
        2. If a user asks a non-medical question (e.g., "Who won the World Cup?", "Write python code for..."), politey REFUSE.
           - Example refusal: "I apologize, but I am specialized in health and disease prediction. I cannot answer general queries outside this domain."
        3. ALWAYS include a disclaimer for specific medical advice: "I am an AI, not a doctor. Please consult a healthcare professional for diagnosis and treatment."
        4. Keep answers concise (under 150 words) unless detailed explanation is requested.
        5. Be empathetic and professional.
        """
        
        # Construct chat history if provided (not implemented fully in this simple version, 
        # but ready for expansion where we'd convert history list to Gemini format)
        chat = model.start_chat(history=[
            {"role": "user", "parts": [system_instruction]},
            {"role": "model", "parts": ["Understood. I am ready to assist with health and application-related queries only."]}
        ])
        
        response = chat.send_message(message)
        
        return {
            "success": True,
            "response": response.text
        }
        
    except ValueError as ve:
        return {
            "success": False,
            "error": str(ve),
            "response": "Configuration Error: API key missing."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": "I'm having trouble connecting right now. Please try again later."
        }

