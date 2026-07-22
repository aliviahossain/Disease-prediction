import csv
import io
import html
import os
import re
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, send_file
from flask_login import current_user
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.middleware import rate_limit
from backend.models.ml_model import ml_model
from backend.services.history_service import save_history
from backend.utils.calculator import bayesian_survival
from backend.utils.gemini_helper import generate_recommendations
from backend.utils.tts_helper import generate_tts_audio

disease_bp = Blueprint("disease", __name__)

# ---------------------------------------------------------------------------
# Security constants
# ---------------------------------------------------------------------------
MAX_DISEASE_NAME_LENGTH = 100
MAX_TTS_LENGTH = 2000
ALLOWED_LANGUAGES = {"english", "hindi", "gujarati", "tamil"}
ALLOWED_TEST_RESULTS = {"positive", "negative"}
ALLOWED_PREDICTION_TYPES = {"bayes", "ml"}
_PRINTABLE_RE = re.compile(r"[^\x20-\x7E]")


def _sanitize_name(value: str) -> str:
    """Strip non-printable characters and enforce length limit."""
    if not isinstance(value, str):
        return ""
    value = _PRINTABLE_RE.sub("", value).strip()
    return value[:MAX_DISEASE_NAME_LENGTH]


def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_diseases():
    csv_path = os.path.join(get_project_root(), "hospital_data.csv")
    diseases = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            diseases = [row["disease"] for row in reader]
        print(f"Loaded {len(diseases)} diseases from CSV")
    except FileNotFoundError:
        print(f"Error: hospital_data.csv not found at {csv_path}")
    except Exception as e:
        print(f"Error loading diseases: {e}")
    return diseases


@disease_bp.route("/")
def home():
    ml_diseases = ml_model.get_available_diseases()
    diseases = [d.replace("_", " ").title() for d in ml_diseases]
    return render_template("home.html", diseases=diseases)


@disease_bp.route("/calculator")
def calculator():
    diseases = load_diseases()
    return render_template("calculator.html", diseases=diseases)


@disease_bp.route("/preset", methods=["POST"])
def preset():
    disease_name = request.json.get("disease")

    if not disease_name:
        return jsonify({"error": "Disease name is required"}), 400

    disease_name = _sanitize_name(disease_name)
    if not disease_name:
        return jsonify({"error": "Invalid disease name"}), 400

    try:
        csv_path = os.path.join(get_project_root(), "hospital_data.csv")

        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["disease"].lower() == disease_name.lower():
                    p_d = float(row["prior_probability"])
                    sensitivity = float(row["sensitivity"])
                    false_pos = 1.0 - float(row["specificity"])

                    try:
                        p_d_given_pos = bayesian_survival(p_d, sensitivity, false_pos)
                    except ValueError as e:
                        return jsonify({"error": str(e)}), 400

                    return jsonify(
                        {
                            "p_d_given_pos": round(p_d_given_pos, 4),
                            "prior": p_d,
                            "sensitivity": sensitivity,
                            "falsePositive": false_pos,
                        }
                    )

        return jsonify({"error": "Disease not found in preset data"}), 404

    except FileNotFoundError:
        return jsonify({"error": "Hospital data file not found"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@disease_bp.route("/disease", methods=["POST"])
def disease():
    data = request.json

    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    required_keys = ["pD", "sensitivity", "falsePositive"]
    missing_keys = [
        key
        for key in required_keys
        if data.get(key) is None or str(data.get(key)).strip() == ""
    ]

    if missing_keys:
        return (
            jsonify({"error": f"Missing required fields: {', '.join(missing_keys)}"}),
            400,
        )

    try:
        p_d = float(data.get("pD"))
        sensitivity = float(data.get("sensitivity"))
        false_pos = float(data.get("falsePositive"))
        test_result = data.get("testResult", "positive").lower()

        for name, value in [
            ("Prevalence", p_d),
            ("Sensitivity", sensitivity),
            ("FalsePositive", false_pos),
        ]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"{name} must be between 0 and 1 (inclusive). Got {value}."
                )

        if test_result not in ALLOWED_TEST_RESULTS:
            raise ValueError('testResult must be either "positive" or "negative".')

        specificity = 1 - false_pos

        if test_result == "positive":
            numerator = sensitivity * p_d
            denominator = numerator + (1 - specificity) * (1 - p_d)
        else:
            numerator = (1 - sensitivity) * p_d
            denominator = numerator + specificity * (1 - p_d)

        if denominator == 0:
            return (
                jsonify(
                    {
                        "error": "Calculation error: Division by zero. Please check your input values."
                    }
                ),
                400,
            )

        p_d_given_result = numerator / denominator

        save_history(
            user_id=current_user.id if current_user.is_authenticated else None,
            prediction_type="bayes",
            disease=data.get("disease_name") or data.get("disease"),
            inputs={
                "pD": p_d,
                "sensitivity": sensitivity,
                "falsePositive": false_pos,
                "testResult": test_result,
            },
            results={"p_d_given_result": p_d_given_result},
            probability=p_d_given_result,
        )

        return jsonify(
            {
                "p_d_given_result": round(p_d_given_result, 4),
                "p_d_given_pos": round(p_d_given_result, 4),
                "test_result": test_result,
            }
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@disease_bp.route("/contact")
def contact():
    return render_template("contact.html")


@disease_bp.route("/gemini-recommendations", methods=["POST"])
@rate_limit("gemini")
def gemini_recommendations():
    data = request.json
    try:
        disease_name = _sanitize_name(data.get("disease_name") or "")
        prior_probability = float(data.get("prior_probability"))
        posterior_probability = float(data.get("posterior_probability"))

        test_result = str(data.get("test_result", "positive")).lower()
        if test_result not in ALLOWED_TEST_RESULTS:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Invalid test_result value. Must be 'positive' or 'negative'.",
                    }
                ),
                400,
            )

        language = str(data.get("language", "english")).lower()
        if language not in ALLOWED_LANGUAGES:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Invalid language. Allowed: {', '.join(sorted(ALLOWED_LANGUAGES))}",
                    }
                ),
                400,
            )

        result = generate_recommendations(
            disease_name=disease_name or None,
            prior_probability=prior_probability,
            posterior_probability=posterior_probability,
            test_result=test_result,
            language=language,
        )

        return jsonify(result)

    except ValueError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Invalid input: {str(e)}",
                    "recommendations": "Unable to generate recommendations. Please check your inputs.",
                }
            ),
            400,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "recommendations": "Unable to generate recommendations. Please try again later.",
                }
            ),
            500,
        )


@disease_bp.route("/download-results", methods=["POST"])
def download_results():
    data = request.json

    try:
        prior = float(data.get("prior_probability", 0))
        posterior = float(data.get("posterior_probability", 0))
        disease_name = (
            _sanitize_name(data.get("disease_name") or "Custom Disease")
            or "Custom Disease"
        )
        disease_name_escaped = html.escape(disease_name)
        test_result = str(data.get("test_result", "positive")).capitalize()
        sensitivity = float(data.get("sensitivity", 0))
        false_positive = float(data.get("false_positive", 0))

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1f77b4"),
            alignment=1,
            spaceAfter=20,
        )

        story = []
        story.append(Paragraph("Possibility Report", title_style))
        story.append(Spacer(1, 0.3 * inch))
        story.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        table_data = [
            ["Parameter", "Value"],
            ["Disease Name", disease_name_escaped],
            ["Prior Probability", f"{prior:.4f}"],
            ["Posterior Probability", f"{posterior:.4f}"],
            ["Test Result", test_result],
            ["Sensitivity", f"{sensitivity:.4f}"],
            ["False Positive Rate", f"{false_positive:.4f}"],
        ]

        table = Table(table_data, colWidths=[3 * inch, 3 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

        risk_level = (
            "High Risk"
            if posterior > 0.7
            else "Moderate Risk" if posterior > 0.3 else "Low Risk"
        )

        story.append(
            Paragraph(f"<b>Risk Assessment:</b> {risk_level}", styles["Normal"])
        )
        story.append(Spacer(1, 0.2 * inch))
        story.append(
            Paragraph(
                "<i>This report is for educational purposes only. "
                "Consult healthcare professionals for medical advice.</i>",
                styles["Normal"],
            )
        )
        doc.title = "Possibility Report"
        doc.build(story)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="Possibility_Report.pdf",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@disease_bp.route("/download-ml-results", methods=["POST"])
def download_ml_results():
    data = request.json

    try:
        disease_name = (
            _sanitize_name(data.get("disease_name") or "Unknown Disease")
            or "Unknown Disease"
        )
        disease_name_escaped = html.escape(disease_name)
        ml_probability = float(data.get("ml_probability", 0))
        prior_probability = float(data.get("prior_probability", 0))
        likelihood = float(data.get("likelihood", 0))
        posterior_probability = float(data.get("posterior_probability", 0))
        risk_level = data.get("risk_level", "Low Risk")
        missing_symptoms = data.get("missing_symptoms", [])

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1f77b4"),
            spaceAfter=12,
            alignment=1,
        )

        story = []
        story.append(
            Paragraph("ML Disease Prediction Report\n(Bayesian Analysis)", title_style)
        )
        story.append(Spacer(1, 0.3 * inch))

        timestamp_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(timestamp_text, styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph(f"<b>Disease:</b> {disease_name_escaped}", styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                f"<b>ML Prediction Probability:</b> {ml_probability:.2%}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        data_table = [
            ["Bayesian Analysis", "Value"],
            ["Prior Probability", f"{prior_probability:.4f}"],
            ["Likelihood", f"{likelihood:.4f}"],
            ["Posterior Probability", f"{posterior_probability:.4f}"],
            ["Risk Assessment", risk_level],
        ]

        table = Table(data_table, colWidths=[2.5 * inch, 2.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f0f0f0")],
                    ),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

        if missing_symptoms:
            story.append(Paragraph("<b>Missing Key Symptoms</b>", styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

            ms_data = [["Symptom", "Importance"]]
            for item in missing_symptoms:
                ms_data.append([item["name"], f"{item['weight'] * 100:.0f}%"])

            ms_table = Table(ms_data, colWidths=[2.5 * inch, 2.5 * inch])
            ms_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e74c3c")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(ms_table)
            story.append(Spacer(1, 0.3 * inch))

        risk_color = (
            "#27ae60"
            if risk_level == "Low Risk"
            else ("#f39c12" if risk_level == "Moderate Risk" else "#e74c3c")
        )
        story.append(
            Paragraph(
                f"<font color='{risk_color}'><b>Risk Level: {risk_level}</b></font>",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        disclaimer = "<i>Note: This report is for educational purposes only. Always consult with healthcare professionals for medical advice.</i>"
        story.append(Paragraph(disclaimer, styles["Normal"]))

        doc.build(story)
        buffer.seek(0)

        filename = (
            f"ml_prediction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@disease_bp.route("/disease-detection-dashboard")
def disease_detection_dashboard():
    types = ["Eyes", "Skin"]
    return render_template("disease_detection_dashboard.html", types=types)


@disease_bp.route("/text-to-speech", methods=["POST"])
def text_to_speech():
    data = request.json
    if not data or not data.get("text"):
        return jsonify({"error": "No text provided for TTS."}), 400

    text = data.get("text", "")

    if not isinstance(text, str) or len(text) > MAX_TTS_LENGTH:
        return (
            jsonify(
                {
                    "error": f"Text exceeds maximum allowed length of {MAX_TTS_LENGTH} characters."
                }
            ),
            400,
        )

    language = str(data.get("language", "english")).lower()
    if language not in ALLOWED_LANGUAGES:
        return (
            jsonify(
                {
                    "error": f"Invalid language. Allowed: {', '.join(sorted(ALLOWED_LANGUAGES))}"
                }
            ),
            400,
        )

    try:
        audio_buffer = generate_tts_audio(text, language)
        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="recommendation.mp3",
        )
    except Exception as e:
        return jsonify({"error": f"TTS generation failed: {str(e)}"}), 500
