from flask import Blueprint, request, jsonify, render_template, send_file
from datetime import datetime
import csv
import os
import io
#pdf generation imports
from reportlab.lib.pagesizes import letter  
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from backend.utils.calculator import bayesian_survival
from backend.utils.gemini_helper import generate_recommendations
from backend.models.ml_model import ml_model

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
        print(f"Loaded {len(diseases)} diseases from CSV")
    except FileNotFoundError:
        print(f"Error: hospital_data.csv not found at {csv_path}")
    except Exception as e:
        print(f"Error loading diseases: {e}")
    return diseases

@disease_bp.route("/")
def home():
    """Render the home page with ML Prediction"""
    # diseases = load_diseases() # OLD: Loaded from CSV
    # NEW: Load only diseases supported by the ML model
    ml_diseases = ml_model.get_available_diseases()
    diseases = [d.replace('_', ' ').title() for d in ml_diseases]
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
                    try:
                        p_d_given_pos = bayesian_survival(p_d, sensitivity, false_pos)
                    except ValueError as e:
                        return jsonify({"error": str(e)}), 400

                    return jsonify({
                        "p_d_given_pos": round(p_d_given_pos, 4),
                        "prior": p_d,
                        "sensitivity": sensitivity,
                        "falsePositive": false_pos
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

@disease_bp.route("/contact")
def contact():
    """Render the Contact page"""
    return render_template("contact.html")

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

#PDF generation route
@disease_bp.route("/download-results", methods=["POST"])
def download_results():
    """Download calculation results as PDF only"""
    data = request.json

    try:
        # Extract calculation data
        prior = float(data.get("prior_probability", 0))
        posterior = float(data.get("posterior_probability", 0))
        disease_name = data.get("disease_name", "Custom Disease")
        test_result = str(data.get("test_result", "positive")).capitalize()
        sensitivity = float(data.get("sensitivity", 0))
        false_positive = float(data.get("false_positive", 0))

        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
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

        # Title
        story.append(Paragraph("Possibility Report", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Timestamp
        story.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        # Results table
        table_data = [
            ["Parameter", "Value"],
            ["Disease Name", disease_name],
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
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

        # Risk assessment
        risk_level = (
            "High Risk" if posterior > 0.7 else
            "Moderate Risk" if posterior > 0.3 else
            "Low Risk"
        )

        story.append(
            Paragraph(f"<b>Risk Assessment:</b> {risk_level}", styles["Normal"])
        )
        story.append(Spacer(1, 0.2 * inch))

        # Disclaimer
        story.append(
            Paragraph(
                "<i>This report is for educational purposes only. "
                "Consult healthcare professionals for medical advice.</i>",
                styles["Normal"],
            )
        )
        doc.title = "Possibility Report"
        doc.build(story)  #  browser tab title / filename
        buffer.seek(0)
        #dowload pdf name
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="Possibility_Report.pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@disease_bp.route("/download-ml-results", methods=["POST"])
def download_ml_results():
    """Download ML prediction results as PDF"""
    data = request.json
    
    try:
        disease_name = data.get("disease_name", "Unknown Disease")
        ml_probability = float(data.get("ml_probability", 0))
        prior_probability = float(data.get("prior_probability", 0))
        likelihood = float(data.get("likelihood", 0))
        posterior_probability = float(data.get("posterior_probability", 0))
        risk_level = data.get("risk_level", "Low Risk")
        missing_symptoms = data.get("missing_symptoms", [])
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=1
        )
        
        story = []
        story.append(Paragraph("ML Disease Prediction Report\n(Bayesian Analysis)", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Add timestamp
        timestamp_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(timestamp_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Disease and ML Prediction
        story.append(Paragraph(f"<b>Disease:</b> {disease_name}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"<b>ML Prediction Probability:</b> {ml_probability:.2%}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Create Bayesian Analysis table
        data_table = [
            ['Bayesian Analysis', 'Value'],
            ['Prior Probability', f"{prior_probability:.4f}"],
            ['Likelihood', f"{likelihood:.4f}"],
            ['Posterior Probability', f"{posterior_probability:.4f}"],
            ['Risk Assessment', risk_level]
        ]
        
        table = Table(data_table, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Add Missing Symptoms Table if present
        if missing_symptoms:
            story.append(Paragraph("<b>Missing Key Symptoms</b>", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            ms_data = [['Symptom', 'Importance']]
            for item in missing_symptoms:
                ms_data.append([item['name'], f"{item['weight']*100:.0f}%"])
                
            ms_table = Table(ms_data, colWidths=[2.5*inch, 2.5*inch])
            ms_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(ms_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Add risk color coding
        risk_color = "#27ae60" if risk_level == "Low Risk" else ("#f39c12" if risk_level == "Moderate Risk" else "#e74c3c")
        story.append(Paragraph(f"<font color='{risk_color}'><b>Risk Level: {risk_level}</b></font>", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Add disclaimer
        disclaimer = "<i>Note: This report is for educational purposes only. Always consult with healthcare professionals for medical advice.</i>"
        story.append(Paragraph(disclaimer, styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        filename = f"ml_prediction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@disease_bp.route('/disease-detection-dashboard')
def disease_detection_dashboard():
    """Render the disease detection dashboard page"""
    # The types include the list of disease detection types available (Only "Eyes" for now)
    types = ["Eyes", "Skin"]
    return render_template('disease_detection_dashboard.html', types=types)