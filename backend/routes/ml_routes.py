import json
import traceback

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user
from jinja2 import TemplateNotFound

from backend import db
from backend.models.ml_model import ml_model
from backend.models.prediction import PredictionHistory
from backend.preprocessing import PreprocessingError, clean_prediction_payload
from backend.services.history_service import save_history
from backend.utils.calculator import BayesCalculator
from backend.utils.uncertainty_handler import uncertainty_handler  # NEW

ml_bp = Blueprint("ml", __name__)


@ml_bp.route("/ml-prediction")
def ml_prediction_page():
    """Render the ML prediction page"""
    try:
        diseases = ml_model.get_available_diseases()
        disease_data = {}

        for disease in diseases:
            disease_data[disease] = {
                "name": disease.replace("_", " ").title(),
                "symptoms": ml_model.get_disease_symptoms(disease),
            }

        return render_template(
            "ml_prediction.html", diseases=disease_data, active_page="ml_prediction"
        )
    except TemplateNotFound as e:
        return render_template("error.html", error=f"Missing template: {e.name}"), 500
    except Exception as e:
        return render_template("error.html", error=str(e)), 500


@ml_bp.route("/api/ml/predict", methods=["POST"])
def predict_disease():
    """
    API endpoint for ML disease prediction.

    Expected JSON payload:
    {
        "disease": "diabetes",
        "symptoms": ["fever", "cough", "fatigue"]
    }

    Response includes is_sufficient and reason so the frontend can render
    the appropriate UI (result card vs. uncertainty warning).
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        disease = data.get("disease", "").lower()
        symptoms = data.get("symptoms", [])
        age = data.get("age")
        height = data.get("height_cm")
        weight = data.get("weight_kg")

        if age is not None:
            try:
                age = int(age)
            except (ValueError, TypeError):
                age = None

        if not disease:
            return jsonify({"error": "Disease not specified"}), 400

        if not symptoms:
            return jsonify({"error": "No symptoms provided"}), 400

        cleaned = clean_prediction_payload(
            data,
            valid_symptoms=(item["key"] for item in ml_model.get_all_unique_symptoms()),
            require_disease=True,
        )
        disease = cleaned.disease
        symptoms = cleaned.symptoms
        age = cleaned.age
        height = cleaned.height_cm
        weight = cleaned.weight_kg

        # Get ML prediction
        ml_prediction = ml_model.predict_disease_probability(
            disease, symptoms, age=age, height_cm=height, weight_kg=weight
        )

        # ── Uncertainty check ─────────────────────────────────────────────
        confidence_score = ml_prediction["confidence_score"]  # 0–1 float
        uncertainty_check = uncertainty_handler.evaluate(
            confidence_score=confidence_score,
        )
        if not uncertainty_check["is_sufficient"]:
            # Return early with a structured "insufficient data" response.
            # The frontend reads is_sufficient=False and renders the warning card.
            return (
                jsonify(
                    {
                        "success": True,
                        "is_sufficient": False,
                        "disease": disease.replace("_", " ").title(),
                        "confidence": round(confidence_score * 100, 2),
                        "reason": uncertainty_check["reason"],
                        "feature_impacts": ml_prediction.get("feature_impacts", []),
                        "explanation_summary": ml_prediction.get(
                            "explanation_summary", ""
                        ),
                    }
                ),
                200,
            )
        # ─────────────────────────────────────────────────────────────────

        # Get missing symptom analysis
        missing_symptoms = ml_model.analyze_missing_symptoms(disease, symptoms)

        # Calculate Bayesian probabilities
        calculator = BayesCalculator()
        bayesian_result = calculator.calculate_posterior(
            prior=ml_prediction["prior_probability"],
            likelihood=ml_prediction["likelihood"],
            false_positive_rate=0.05,
        )

        # Determine risk level for storage
        risk_assessment = get_risk_level(bayesian_result["posterior"] * 100)
        risk_level_map = {
            "Low": "low",
            "Moderate": "medium",
            "High": "high",
            "Critical": "critical",
        }
        risk_level_db = risk_level_map.get(risk_assessment["level"], "medium")

        # Save prediction to database
        vitals_analysis = {
            "vitals_health_score": 1.0,
            "summary": "Vitals not provided.",
            "flags": [],
        }
        survival_prob = round((1.0 - bayesian_result["posterior"]) * 100, 2)

        try:
            from backend.utils.temporal_analysis import TemporalAnalysisEngine

            # Analyze current vitals
            vitals_analysis = TemporalAnalysisEngine.analyze_vitals(
                heart_rate=cleaned.heart_rate,
                bp_systolic=cleaned.blood_pressure_systolic,
                bp_diastolic=cleaned.blood_pressure_diastolic,
                blood_glucose=cleaned.blood_glucose,
                temperature=cleaned.temperature,
            )

            # Calculate trend factor if logged in and has past predictions
            trend_factor = 0.0
            if current_user.is_authenticated:
                user_preds = (
                    PredictionHistory.query.filter_by(user_id=current_user.id)
                    .order_by(PredictionHistory.created_at.desc())
                    .all()
                )
                if user_preds:
                    prev_rec = user_preds[0]
                    prev_vitals = TemporalAnalysisEngine.analyze_vitals(
                        heart_rate=prev_rec.heart_rate,
                        bp_systolic=prev_rec.blood_pressure_systolic,
                        bp_diastolic=prev_rec.blood_pressure_diastolic,
                        blood_glucose=prev_rec.blood_glucose,
                        temperature=prev_rec.temperature,
                    )
                    diff = (
                        vitals_analysis["vitals_health_score"]
                        - prev_vitals["vitals_health_score"]
                    )
                    trend_factor = max(-0.15, min(0.15, diff * 0.3))

            survival_prob = TemporalAnalysisEngine.calculate_dynamic_survival(
                disease_posterior=bayesian_result["posterior"],
                vitals_health_score=vitals_analysis["vitals_health_score"],
                trend_factor=trend_factor,
            )

            # Only persist history for authenticated users.
            # Storing records with user_id=None leaks sensitive health data
            # (vitals, diagnoses) with no data subject linkage, making it
            # impossible to honour deletion requests and causing the table
            # to grow unboundedly with orphaned rows.
            if current_user.is_authenticated:
                prediction_record = PredictionHistory(
                    user_id=current_user.id,
                    disease=disease,
                    symptoms=json.dumps(symptoms),
                    patient_age=age,
                    ml_probability=ml_prediction["raw_probability"],
                    bayesian_posterior=bayesian_result["posterior"],
                    confidence_score=confidence_score,
                    survival_probability=survival_prob,
                    heart_rate=cleaned.heart_rate,
                    blood_pressure_systolic=cleaned.blood_pressure_systolic,
                    blood_pressure_diastolic=cleaned.blood_pressure_diastolic,
                    blood_glucose=cleaned.blood_glucose,
                    temperature=cleaned.temperature,
                    risk_level=risk_level_db,
                )
                db.session.add(prediction_record)
                db.session.commit()
                print(
                    f"Prediction saved: disease={disease}, risk_level={risk_level_db}, survival_prob={survival_prob}%"
                )
        except Exception as db_error:
            print(f"Failed to save prediction to database: {db_error}")
            traceback.print_exc()
            db.session.rollback()

        # Build full result (only reached when prediction is confident)
        result = {
            "success": True,
            "is_sufficient": True,  # NEW — frontend uses this flag
            "disease": disease.replace("_", " ").title(),
            "bmi": ml_prediction.get("bmi"),
            "bmi_category": ml_prediction.get("bmi_category"),
            "preprocessing": cleaned.metadata(),
            "temporal_analysis": {
                "survival_probability": survival_prob,
                "vitals_health_score": round(
                    vitals_analysis["vitals_health_score"] * 100, 1
                ),
                "vitals_summary": vitals_analysis["summary"],
                "flags": vitals_analysis["flags"],
            },
            "ml_prediction": {
                "raw_probability": round(
                    ml_prediction.get("raw_probability", 0) * 100, 2
                ),
                "calibrated_probability": (
                    round(ml_prediction.get("calibrated_probability", 0) * 100, 2)
                    if ml_prediction.get("calibrated_probability") is not None
                    else None
                ),
                "calibration_gap": (
                    round(ml_prediction.get("calibration_gap", 0) * 100, 2)
                    if ml_prediction.get("calibration_gap") is not None
                    else None
                ),
                "calibration_score": (
                    round(ml_prediction.get("calibration_score", 0) * 100, 2)
                    if ml_prediction.get("calibration_score") is not None
                    else None
                ),
                "confidence_score": round(confidence_score * 100, 2),
                "symptoms_analyzed": ml_prediction.get("symptoms_matched", []),
                "missing_symptoms": missing_symptoms,
                "explanations": {
                    "feature_impacts": ml_prediction.get("feature_impacts", []),
                    "symptom_contributions": ml_prediction.get("symptom_contributions", {}),
                    "summary": ml_prediction.get("explanation_summary", ""),
                    "bias": ml_prediction.get("bias"),
                    "bmi_effect": ml_prediction.get("bmi_effect"),
                },
            },
            "bayesian_analysis": {
                "prior": round(bayesian_result["prior"] * 100, 2),
                "likelihood": round(bayesian_result["likelihood"] * 100, 2),
                "posterior": round(bayesian_result["posterior"] * 100, 2),
                "false_positive_rate": round(
                    bayesian_result["false_positive_rate"] * 100, 2
                ),
            },
            "risk_assessment": risk_assessment,
        }

        # Persist via the unified history service so the History page
        # (PatientHistory) shows this prediction. Only written for
        # authenticated users to avoid orphaned anonymous health records.
        if current_user.is_authenticated:
            save_history(
                user_id=current_user.id,
                prediction_type="symptom",
                disease=disease.replace("_", " ").title(),
                inputs={
                    "symptoms": symptoms,
                    "age": age,
                    "height_cm": height,
                    "weight_kg": weight,
                },
                results={
                    "ml_probability": ml_prediction["raw_probability"],
                    "bayesian_posterior": bayesian_result["posterior"],
                    "confidence_score": confidence_score,
                    "survival_probability": survival_prob,
                },
                probability=bayesian_result["posterior"],
                risk_level=risk_level_db,
            )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@ml_bp.route("/api/ml/predict-multiple", methods=["POST"])
def predict_multiple_diseases():
    """
    API endpoint for differential diagnosis (predict multiple diseases).

    Expected JSON payload:
    {
        "symptoms": ["fever", "cough", "fatigue"]
    }

    Each result in the list includes is_sufficient so the frontend can
    visually distinguish low-confidence entries in the comparison table.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        symptoms = data.get("symptoms", [])

        if not symptoms:
            return jsonify({"error": "No symptoms provided"}), 400

        age = data.get("age")
        height = data.get("height_cm")
        weight = data.get("weight_kg")

        cleaned = clean_prediction_payload(
            data,
            valid_symptoms=(item["key"] for item in ml_model.get_all_unique_symptoms()),
            require_disease=False,
        )
        symptoms = cleaned.symptoms
        age = cleaned.age
        height = cleaned.height_cm
        weight = cleaned.weight_kg

        predictions = ml_model.predict_multiple_diseases(
            symptoms, age=age, height_cm=height, weight_kg=weight
        )

        # Format results
        results = []
        calculator = BayesCalculator()

        # Sort by confidence descending so we can compare rank-1 vs rank-2
        predictions.sort(key=lambda p: p["confidence_score"], reverse=True)

        for i, pred in enumerate(predictions):
            bayesian = calculator.calculate_posterior(
                prior=pred["prior_probability"],
                likelihood=pred["likelihood"],
                false_positive_rate=0.05,
            )

            missing = ml_model.analyze_missing_symptoms(pred["disease"], symptoms)

            confidence_score = pred["confidence_score"]
            top2_score = (
                predictions[i + 1]["confidence_score"]
                if i + 1 < len(predictions)
                else None
            )
            top2_disease = (
                predictions[i + 1]["disease"].replace("_", " ").title()
                if top2_score
                else None
            )

            # ── Uncertainty check per disease entry ──────────────────────
            uncertainty_check = uncertainty_handler.evaluate(
                confidence_score=confidence_score,
                top2_score=top2_score,
                disease_name=pred["disease"].replace("_", " ").title(),
                top2_disease=top2_disease or "",
            )
            # ─────────────────────────────────────────────────────────────

            top_prediction = {
                "disease": pred["disease"].replace("_", " ").title(),
                "probability": round(pred["raw_probability"] * 100, 2),
                "prior": round(bayesian["prior"] * 100, 2),
                "likelihood": round(bayesian["likelihood"] * 100, 2),
                "posterior": round(bayesian["posterior"] * 100, 2),
                "confidence": round(confidence_score * 100, 2),
                "risk_level": get_risk_level(bayesian["posterior"] * 100),
                "missing_symptoms": missing,
                "feature_impacts": pred.get("feature_impacts", []),
                "explanation_summary": pred.get("explanation_summary", ""),
                "symptom_contributions": pred.get("symptom_contributions", {}),
                "bias": pred.get("bias", 0),
                "bmi_effect": pred.get("bmi_effect", 0),
                "explanations": {
                    "feature_impacts": pred.get("feature_impacts", []),
                    "symptom_contributions": pred.get("symptom_contributions", {}),
                    "summary": pred.get("explanation_summary", ""),
                    "bias": pred.get("bias", 0),
                    "bmi_effect": pred.get("bmi_effect", 0),
                },
                # NEW — uncertainty fields
                "is_sufficient": uncertainty_check["is_sufficient"],
                "uncertainty_reason": uncertainty_check["reason"],
            }
            results.append(top_prediction)

        # Sort by posterior probability (highest first)
        results.sort(key=lambda x: x["posterior"], reverse=True)
        top_predictions = results[:5]

        # If user is authenticated, save the top prediction to history to enable temporal progression tracking!
        if current_user.is_authenticated and top_predictions:
            try:
                top_pred = top_predictions[0]
                # Normalize disease key
                disease_key = top_pred["disease"].lower().replace(" ", "_")

                from backend.utils.temporal_analysis import \
                    TemporalAnalysisEngine

                # Analyze current vitals
                vitals_analysis = TemporalAnalysisEngine.analyze_vitals(
                    heart_rate=cleaned.heart_rate,
                    bp_systolic=cleaned.blood_pressure_systolic,
                    bp_diastolic=cleaned.blood_pressure_diastolic,
                    blood_glucose=cleaned.blood_glucose,
                    temperature=cleaned.temperature,
                )

                # Calculate trend factor from prior predictions
                trend_factor = 0.0
                user_preds = (
                    PredictionHistory.query.filter_by(user_id=current_user.id)
                    .order_by(PredictionHistory.created_at.desc())
                    .all()
                )
                if user_preds:
                    prev_rec = user_preds[0]
                    prev_vitals = TemporalAnalysisEngine.analyze_vitals(
                        heart_rate=prev_rec.heart_rate,
                        bp_systolic=prev_rec.blood_pressure_systolic,
                        bp_diastolic=prev_rec.blood_pressure_diastolic,
                        blood_glucose=prev_rec.blood_glucose,
                        temperature=prev_rec.temperature,
                    )
                    diff = (
                        vitals_analysis["vitals_health_score"]
                        - prev_vitals["vitals_health_score"]
                    )
                    trend_factor = max(-0.15, min(0.15, diff * 0.3))

                # Dynamic survival probability
                posterior_prob = top_pred["posterior"] / 100.0
                survival_prob = TemporalAnalysisEngine.calculate_dynamic_survival(
                    disease_posterior=posterior_prob,
                    vitals_health_score=vitals_analysis["vitals_health_score"],
                    trend_factor=trend_factor,
                )

                risk_level_map = {
                    "Low": "low",
                    "Moderate": "medium",
                    "High": "high",
                    "Critical": "critical",
                }
                risk_level_db = risk_level_map.get(
                    top_pred["risk_level"]["level"], "medium"
                )

                prediction_record = PredictionHistory(
                    user_id=current_user.id,
                    disease=disease_key,
                    symptoms=json.dumps(symptoms),
                    patient_age=age,
                    ml_probability=top_pred["probability"] / 100.0,
                    bayesian_posterior=posterior_prob,
                    confidence_score=top_pred["confidence"] / 100.0,
                    survival_probability=survival_prob,
                    heart_rate=cleaned.heart_rate,
                    blood_pressure_systolic=cleaned.blood_pressure_systolic,
                    blood_pressure_diastolic=cleaned.blood_pressure_diastolic,
                    blood_glucose=cleaned.blood_glucose,
                    temperature=cleaned.temperature,
                    risk_level=risk_level_db,
                )
                db.session.add(prediction_record)
                db.session.commit()
                print(
                    f"✅ Auto-saved home page top prediction to history: {disease_key}, risk={risk_level_db}, survival_prob={survival_prob}%"
                )
            except Exception as db_err:
                print(f"⚠️ Failed to auto-save prediction: {db_err}")
                traceback.print_exc()
                db.session.rollback()

         # Issue #230: also persist the top prediction via the unified
        # history service so the PatientHistory-backed History page
        # reflects this differential diagnosis run.
        if top_predictions and current_user.is_authenticated:
            top_pred = top_predictions[0]
            top_risk = top_pred.get("risk_level") or {}
            save_history(
                user_id=current_user.id,
                prediction_type="symptom",
                disease=top_pred["disease"],
                inputs={
                    "symptoms": symptoms,
                    "age": age,
                    "height_cm": height,
                    "weight_kg": weight,
                    "differential": True,
                },
                results={
                    "top_predictions": [
                        {
                            "disease": p["disease"],
                            "posterior": p["posterior"],
                            "confidence": p["confidence"],
                        }
                        for p in top_predictions
                    ],
                },
                probability=top_pred["posterior"] / 100.0,
                risk_level=(top_risk.get("level") or "").lower() or None,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "predictions": top_predictions,
                    "symptoms_count": len(symptoms),
                    "preprocessing": cleaned.metadata(),
                    "total_diseases_checked": len(predictions),
                }
            ),
            200,
        )

    except PreprocessingError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@ml_bp.route("/api/ml/diseases", methods=["GET"])
def get_diseases():
    """Get list of available diseases"""
    try:
        diseases = ml_model.get_available_diseases()
        disease_list = [
            {"key": disease, "name": disease.replace("_", " ").title()}
            for disease in diseases
        ]
        return jsonify({"success": True, "diseases": disease_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/api/ml/symptoms/<disease>", methods=["GET"])
def get_disease_symptoms(disease):
    """Get symptoms for a specific disease"""
    try:
        symptoms = ml_model.get_disease_symptoms(disease.lower())
        symptom_list = [{"key": key, "name": name} for key, name in symptoms.items()]
        return (
            jsonify(
                {
                    "success": True,
                    "disease": disease.replace("_", " ").title(),
                    "symptoms": symptom_list,
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/api/ml/symptoms", methods=["GET"])
def get_all_symptoms():
    """Get all unique symptoms across all diseases"""
    try:
        symptoms = ml_model.get_all_unique_symptoms()
        return (
            jsonify({"success": True, "symptoms": symptoms, "count": len(symptoms)}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ml_bp.route("/api/ml/symptom-importance/<disease>", methods=["GET"])
def get_symptom_importance(disease):
    """Get symptom importance/weights for a disease"""
    try:
        importance = ml_model.get_symptom_importance(disease.lower())
        importance_list = [
            {"symptom": symptom, "importance": round(weight * 100, 1)}
            for symptom, weight in importance.items()
        ]
        return (
            jsonify(
                {
                    "success": True,
                    "disease": disease.replace("_", " ").title(),
                    "symptom_importance": importance_list,
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/api/ml/config", methods=["GET"])
def get_uncertainty_config():
    """
    Return the active uncertainty thresholds.
    Useful for admin dashboards and documentation.
    """
    return jsonify(uncertainty_handler.get_config()), 200


@ml_bp.route("/api/ml/explain", methods=["POST"])
def explain_prediction():
    """SHAP-based prediction explainability endpoint."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        disease = data.get("disease", "").lower().replace(" ", "_")
        symptoms = data.get("symptoms", [])

        if not disease:
            return jsonify({"error": "Disease not specified"}), 400
        if not symptoms:
            return jsonify({"error": "No symptoms provided"}), 400

        disease_key = ml_model._get_disease_key(disease)
        prediction = ml_model.predict_disease_probability(disease, symptoms)
        shap_values = ml_model.compute_shap_values(disease_key, symptoms)

        positive = {
            k: v for k, v in shap_values.items() if v["direction"] == "positive"
        }
        negative = {
            k: v for k, v in shap_values.items() if v["direction"] == "negative"
        }

        top_positive = sorted(
            positive.items(), key=lambda x: x[1]["contribution"], reverse=True
        )[:3]

        summary_parts = [
            f"{v['display_name']} (+{v['contribution']:.2f})" for _, v in top_positive
        ]
        summary = (
            f"Top contributing symptoms: {', '.join(summary_parts)}"
            if summary_parts
            else "No strong symptom contributions found."
        )

        return (
            jsonify(
                {
                    "success": True,
                    "disease": disease.replace("_", " ").title(),
                    "calibrated_probability": round(
                        prediction["calibrated_probability"] * 100, 2
                    ),
                    "explanation": {
                        "shap_values": shap_values,
                        "positive_contributions": positive,
                        "negative_contributions": negative,
                        "summary": summary,
                        "baseline_info": (
                            "Positive values increase disease probability. "
                            "Negative values indicate important absent symptoms."
                        ),
                    },
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Explanation failed: {str(e)}"}), 500


def get_risk_level(probability):
    """
    Determine risk level based on probability percentage.

    Args:
        probability: Probability percentage (0-100)

    Returns:
        Dictionary with risk level and color
    """
    if probability < 30:
        return {
            "level": "Low",
            "color": "success",
            "description": "Low probability of disease",
        }
    elif probability < 60:
        return {
            "level": "Moderate",
            "color": "warning",
            "description": "Moderate probability - consider further testing",
        }
    elif probability < 85:
        return {
            "level": "High",
            "color": "danger",
            "description": "High probability - immediate medical consultation recommended",
        }
    else:
        return {
            "level": "Critical",
            "color": "dark",
            "description": "Critical risk level - urgent medical attention required",
        }