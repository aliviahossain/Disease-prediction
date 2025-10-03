from flask import Blueprint, request, jsonify, render_template
import csv
import os

from backend.utils.calculator import bayesian_survival

disease_bp = Blueprint("disease", __name__)

@disease_bp.route("/")
def home():
    return render_template("index.html")


@disease_bp.route("/preset", methods=["POST"])
def preset():
    disease_name = request.json.get("disease")
    try:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "hospital_data.csv")
        with open(csv_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["Disease"].lower() == disease_name.lower():
                    p_d = float(row["Prevalence"])
                    sensitivity = float(row["Sensitivity"])
                    false_pos = float(row["FalsePositive"])

                    # Bayes' Theorem calculation (using utility)
                    p_pos = (sensitivity * p_d) + (false_pos * (1 - p_d))
                    p_d_given_pos = bayesian_survival(p_d, sensitivity, false_pos)

                    return jsonify({
                        "p_d_given_pos": round(p_d_given_pos, 4)
                    })

        return jsonify({"error": "Disease not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@disease_bp.route("/disease", methods=["POST"])
def disease():
    data = request.json
    try:
        # Input extraction
        p_d = float(data.get("pD"))
        sensitivity = float(data.get("sensitivity"))
        false_pos = float(data.get("falsePositive"))
        test_result = data.get("testResult", "positive").lower()  # default to positive if not provided

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
            raise ValueError("Inputs lead to an undefined calculation (division by zero).")

        p_d_given_result = numerator / denominator

        return jsonify({
            "p_d_given_result": round(p_d_given_result, 4),
            "test_result": test_result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400
        @disease_bp.route("/scalability")
        def scalability():
         return render_template("scalability.html")

