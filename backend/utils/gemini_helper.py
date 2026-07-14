"""
Gemini API helper for generating recommendations based on disease probability results.
"""
 
import os
from typing import Optional
from google.genai import types
import logging
# Global client variable to keep configuration simple
client = None
token_limit = 2000
logger = logging.getLogger(__name__)
 
def configure_gemini():
    """Configure Gemini API with the API key from environment variables."""
    global client
    try:
        from google import genai
    except ImportError:
        import warnings
 
        warnings.warn(
            "google-genai package not properly installed. Gemini features disabled."
        )
        return
 
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    # Initialize the new SDK client instance
    client = genai.Client(api_key=api_key)
 
 
def generate_recommendations(
    disease_name: Optional[str],
    prior_probability: float,
    posterior_probability: float,
    test_result: str = "positive",
    language: str = "english",
) -> dict:
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
 
        # Try newer models first, fall back to older ones if needed
        model_names = ["gemini-2.5-flash", "gemini-2.5-pro"]
 
        # Construct the prompt
        disease_context = (
            f"the disease '{disease_name}'" if disease_name else "a disease"
        )
 
        # Language mapping for prompt instructions
        language_instructions = {
            "english": "Respond in English.",
            "hindi": "Respond in Hindi (हिंदी में जवाब दें). Use Devanagari script.",
            "gujarati": "Respond in Gujarati (ગુજરાતીમાં જવાબ આપો). Use Gujarati script.",
            "tamil": "Respond in Tamil (தமிழில் பதிலளிக்கவும்). Use Tamil script.",
        }
 
        language_instruction = language_instructions.get(
            language.lower(), language_instructions["english"]
        )
 
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
 
        # Attempt each model in order; move to next if one fails
        last_exception = None
        result = None
 
        for model_name in model_names:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                result = {
                    "success": True,
                    "recommendations": response.text,
                    "prior_probability": prior_probability,
                    "posterior_probability": posterior_probability,
                }
                break
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}. Trying next model...")
                last_exception = e
                continue
 
        if result is None:
            raise last_exception
 
        return result
 
    except ValueError as ve:
        return {
            "success": False,
            "error": str(ve),
            "recommendations": "API key not configured. Please set GEMINI_API_KEY environment variable.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "recommendations": "Unable to generate recommendations at this time. Please try again later.",
        }
 
 
def process_history(messages):
    try:
        tokens = 0  # Considering 1 word ~ 1 token
 
        formatted_history = []
        for turn in messages[-2::-1]:
            if formatted_history and tokens + len(turn['text']) >= token_limit:
                break
            tokens += len(turn['text'])
            formatted_history.append(
                types.Content(
                    role=turn["role"],  # Must be 'user' or 'model'
                    parts=[types.Part.from_text(text=turn["text"])]  # Wrapped properly
                )
            )
        return formatted_history[::-1]
    except Exception as e:
        logger.error(str(e))
        return []
 
 
def generate_chat_response(messages: str, history: list = None) -> dict:
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
 
        # System instruction to restrict domain
        system_instruction = """
        You are a helpful AI assistant for a Disease Prediction Application.
 
        YOUR ROLE:
        - Helper users understand disease predictions.
        - Answer general health and medical questions.
        - Explain how to use the application (symptom checker, calculator, etc.).
        
        STRICT RULES:
        1. ONLY answer questions related to health, medicine, diseases, symptoms, treatments, and this application.
        2. If a user asks a non-medical question (e.g., "Who won the World Cup?", "Write python code for..."), politely REFUSE.
           - Example refusal: "I apologize, but I am specialized in health and disease prediction. I cannot answer general queries outside this domain."
        3. ALWAYS include a disclaimer for specific medical advice: "I am an AI, not a doctor. Please consult a healthcare professional for diagnosis and treatment."
        4. Keep answers concise (under 150 words) unless detailed explanation is requested.
        5. Be empathetic and professional.
        """
        formatted_history = process_history(messages=messages)
 
        # Use the modern chats utility instance configuration passing system instruction
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(system_instruction=system_instruction),
            history=formatted_history
        )
        message = messages[-1].get('text')
 
        response = chat.send_message(message)
 
        return {"success": True, "response": response.text}
 
    except ValueError as ve:
        return {
            "success": False,
            "error": str(ve),
            "response": "Configuration Error: API key missing.",
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "response": "I'm having trouble connecting right now. Please try again later.",
        }
 