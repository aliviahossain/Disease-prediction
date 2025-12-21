from flask import Blueprint, request, jsonify, render_template
import csv
import os

from backend.utils.calculator import bayesian_survival
from backend.utils.gemini_helper import generate_recommendations

disease_bp = Blueprint("disease", __name__)

def get_project_root():
    """Helper function to get the project root directory"""
    # Go up from backend/routes/ to project root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_diseases():
    """Helper function to load diseases from CSV"""
    csv_path = os.path.join(get_project_root(), "hospital_data.csv")
    diseases = []
    try:
        with open(csv_path, newline="", encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            diseases = [row["Disease"] for row in reader]
        print(f"✅ Loaded {len(diseases)} diseases from CSV")
    except FileNotFoundError:
        print(f"⚠️ Error: hospital_data.csv not found at {csv_path}")
    except Exception as e:
        print(f"⚠️ Error loading diseases: {e}")
    return diseases

@disease_bp.route("/")
def home():
    """Render the home page with ML Prediction"""
    diseases = load_diseases()
    return render_template("home.html", diseases=diseases)


@disease_bp.route("/calculator")
def calculator():
    """Render the calculator page (Bayesian calculator)"""
    diseases = load_diseases()
    return render_template("calculator.html", diseases=diseases)


@disease_bp.route("/preset", methods=["POST"])
def preset():
    """Handle preset disease selection"""
    disease_name = request.json.get("disease")
    
    if not disease_name:
        return jsonify({"error": "Disease name is required"}), 400
    
    try:
        csv_path = os.path.join(get_project_root(), "hospital_data.csv")
        
        with open(csv_path, newline="", encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["Disease"].lower() == disease_name.lower():
                    p_d = float(row["Prevalence"])
                    sensitivity = float(row["Sensitivity"])
                    false_pos = float(row["FalsePositive"])

                    # Bayes' Theorem calculation (using utility)
                    p_d_given_pos = bayesian_survival(p_d, sensitivity, false_pos)

                    return jsonify({
                        "p_d_given_pos": round(p_d_given_pos, 4),
                        "prior": p_d 
                    })

        return jsonify({"error": "Disease not found"}), 404

    except FileNotFoundError:
        return jsonify({"error": "Hospital data file not found"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@disease_bp.route("/disease", methods=["POST"])
def disease():
    """Calculate disease probability based on test results"""
    data = request.json
    try:
        # Input extraction
        p_d = float(data.get("pD"))
        sensitivity = float(data.get("sensitivity"))
        false_pos = float(data.get("falsePositive"))
        test_result = data.get("testResult", "positive").lower()

        # Input validation
        for name, value in [("Prevalence", p_d), ("Sensitivity", sensitivity), ("FalsePositive", false_pos)]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be between 0 and 1 (inclusive). Got {value}.")

        if test_result not in {"positive", "negative"}:
            raise ValueError('testResult must be either "positive" or "negative".')

        specificity = 1 - false_pos

        # Bayes' Theorem calculation for both positive and negative results
        if test_result == "positive":
            numerator = sensitivity * p_d
            denominator = numerator + (1 - specificity) * (1 - p_d)
        else:  # negative
            numerator = (1 - sensitivity) * p_d
            denominator = numerator + specificity * (1 - p_d)

        if denominator == 0:
            return jsonify({
                "error": "Calculation error: Division by zero. Please check your input values."
            }), 400

        p_d_given_result = numerator / denominator

        return jsonify({
            "p_d_given_result": round(p_d_given_result, 4),
            "test_result": test_result
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@disease_bp.route("/gemini-recommendations", methods=["POST"])
def gemini_recommendations():
    """
    Generate AI-powered recommendations using Gemini API based on the calculation results.
    """
    data = request.json
    try:
        disease_name = data.get("disease_name")  # Optional, can be None
        prior_probability = float(data.get("prior_probability"))
        posterior_probability = float(data.get("posterior_probability"))
        test_result = data.get("test_result", "positive")
        language = data.get("language", "english")  # Default to English
        
        # Call Gemini API
        result = generate_recommendations(
            disease_name=disease_name,
            prior_probability=prior_probability,
            posterior_probability=posterior_probability,
            test_result=test_result,
            language=language
        )
        
        return jsonify(result)
    
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid input: {str(e)}",
            "recommendations": "Unable to generate recommendations. Please check your inputs."
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "recommendations": "Unable to generate recommendations. Please try again later."
        }), 500