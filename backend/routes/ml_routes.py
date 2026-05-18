from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from backend.models.ml_model import ml_model
from backend.utils.calculator import BayesCalculator
from backend.utils.uncertainty_handler import uncertainty_handler  # NEW
from backend.models.prediction import PredictionHistory
from backend import db
import json
import traceback
 
ml_bp = Blueprint('ml', __name__)
 
 
@ml_bp.route('/ml-prediction')
def ml_prediction_page():
    """Render the ML prediction page"""
    try:
        diseases = ml_model.get_available_diseases()
        disease_data = {}
 
        for disease in diseases:
            disease_data[disease] = {
                'name': disease.replace('_', ' ').title(),
                'symptoms': ml_model.get_disease_symptoms(disease)
            }
 
        return render_template('ml_prediction.html',
                               diseases=disease_data,
                               active_page='ml_prediction')
    except Exception as e:
        return render_template('error.html', error=str(e)), 500
 
 
@ml_bp.route('/api/ml/predict', methods=['POST'])
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
            return jsonify({'error': 'No data provided'}), 400
 
        disease = data.get('disease', '').lower()
        symptoms = data.get('symptoms', [])
        age = data.get('age')
        height = data.get('height_cm')
        weight = data.get('weight_kg')
 
        if age is not None:
            try:
                age = int(age)
            except (ValueError, TypeError):
                age = None
 
        if not disease:
            return jsonify({'error': 'Disease not specified'}), 400
 
        if not symptoms:
            return jsonify({'error': 'No symptoms provided'}), 400
 
        # Get ML prediction
        ml_prediction = ml_model.predict_disease_probability(
            disease, symptoms, age=age, height_cm=height, weight_kg=weight
        )
 
        # ── Uncertainty check ─────────────────────────────────────────────
        confidence_score = ml_prediction['confidence_score']   # 0–1 float
        uncertainty_check = uncertainty_handler.evaluate(
            confidence_score=confidence_score,
        )
 
        if not uncertainty_check['is_sufficient']:
            # Return early with a structured "insufficient data" response.
            # The frontend reads is_sufficient=False and renders the warning card.
            return jsonify({
                'success': True,
                'is_sufficient': False,
                'disease': disease.replace('_', ' ').title(),
                'confidence': round(confidence_score * 100, 2),
                'reason': uncertainty_check['reason'],
            }), 200
        # ─────────────────────────────────────────────────────────────────
 
        # Get missing symptom analysis
        missing_symptoms = ml_model.analyze_missing_symptoms(disease, symptoms)
 
        # Calculate Bayesian probabilities
        calculator = BayesCalculator()
        bayesian_result = calculator.calculate_posterior(
            prior=ml_prediction['prior_probability'],
            likelihood=ml_prediction['likelihood'],
            false_positive_rate=0.05
        )
 
        # Determine risk level for storage
        risk_assessment = get_risk_level(bayesian_result['posterior'] * 100)
        risk_level_map = {'Low': 'low', 'Moderate': 'medium', 'High': 'high', 'Critical': 'critical'}
        risk_level_db = risk_level_map.get(risk_assessment['level'], 'medium')
 
        # Save prediction to database
        try:
            prediction_record = PredictionHistory(
                user_id=current_user.id if current_user.is_authenticated else None,
                disease=disease,
                symptoms=json.dumps(symptoms),
                patient_age=age,
                ml_probability=ml_prediction['raw_probability'],
                bayesian_posterior=bayesian_result['posterior'],
                confidence_score=confidence_score,
                risk_level=risk_level_db
            )
            db.session.add(prediction_record)
            db.session.commit()
            print(f"✅ Prediction saved: disease={disease}, risk_level={risk_level_db}")
        except Exception as db_error:
            print(f"⚠️ Failed to save prediction to database: {db_error}")
            traceback.print_exc()
            db.session.rollback()
 
        # Build full result (only reached when prediction is confident)
        result = {
            'success': True,
            'is_sufficient': True,   # NEW — frontend uses this flag
            'disease': disease.replace('_', ' ').title(),
            'bmi': ml_prediction.get('bmi'),
            'bmi_category': ml_prediction.get('bmi_category'),
            'ml_prediction': {
                'raw_probability': round(ml_prediction['raw_probability'] * 100, 2),
                'confidence_score': round(confidence_score * 100, 2),
                'symptoms_analyzed': ml_prediction['symptoms_matched'],
                'missing_symptoms': missing_symptoms
            },
            'bayesian_analysis': {
                'prior': round(bayesian_result['prior'] * 100, 2),
                'likelihood': round(bayesian_result['likelihood'] * 100, 2),
                'posterior': round(bayesian_result['posterior'] * 100, 2),
                'false_positive_rate': round(bayesian_result['false_positive_rate'] * 100, 2)
            },
            'risk_assessment': risk_assessment
        }
 
        return jsonify(result), 200
 
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500
 
 
@ml_bp.route('/api/ml/predict-multiple', methods=['POST'])
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
            return jsonify({'error': 'No data provided'}), 400
 
        symptoms = data.get('symptoms', [])
 
        if not symptoms:
            return jsonify({'error': 'No symptoms provided'}), 400
 
        age = data.get('age')
        height = data.get('height_cm')
        weight = data.get('weight_kg')
 
        predictions = ml_model.predict_multiple_diseases(
            symptoms, age=age, height_cm=height, weight_kg=weight
        )
 
        results = []
        calculator = BayesCalculator()
 
        # Sort by confidence descending so we can compare rank-1 vs rank-2
        predictions.sort(key=lambda p: p['confidence_score'], reverse=True)
 
        for i, pred in enumerate(predictions):
            bayesian = calculator.calculate_posterior(
                prior=pred['prior_probability'],
                likelihood=pred['likelihood'],
                false_positive_rate=0.05
            )
 
            missing = ml_model.analyze_missing_symptoms(pred['disease'], symptoms)
 
            confidence_score = pred['confidence_score']
            top2_score = predictions[i + 1]['confidence_score'] if i + 1 < len(predictions) else None
            top2_disease = predictions[i + 1]['disease'].replace('_', ' ').title() if top2_score else None
 
            # ── Uncertainty check per disease entry ──────────────────────
            uncertainty_check = uncertainty_handler.evaluate(
                confidence_score=confidence_score,
                top2_score=top2_score,
                disease_name=pred['disease'].replace('_', ' ').title(),
                top2_disease=top2_disease or '',
            )
            # ─────────────────────────────────────────────────────────────
 
            results.append({
                'disease': pred['disease'].replace('_', ' ').title(),
                'probability': round(pred['raw_probability'] * 100, 2),
                'prior': round(bayesian['prior'] * 100, 2),
                'likelihood': round(bayesian['likelihood'] * 100, 2),
                'posterior': round(bayesian['posterior'] * 100, 2),
                'confidence': round(confidence_score * 100, 2),
                'risk_level': get_risk_level(bayesian['posterior'] * 100),
                'missing_symptoms': missing,
                'explanations': {
                    'symptom_contributions': pred.get('symptom_contributions', {'test_symptom': 0.1}),
                    'bias': pred.get('bias', 0),
                    'bmi_effect': pred.get('bmi_effect', 0)
                },
                # NEW — uncertainty fields
                'is_sufficient': uncertainty_check['is_sufficient'],
                'uncertainty_reason': uncertainty_check['reason'],
            })
 
        # Sort by posterior probability (highest first)
        results.sort(key=lambda x: x['posterior'], reverse=True)
        top_predictions = results[:5]
 
        return jsonify({
            'success': True,
            'predictions': top_predictions,
            'symptoms_count': len(symptoms),
            'total_diseases_checked': len(predictions)
        }), 200
 
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500
 
 
@ml_bp.route('/api/ml/diseases', methods=['GET'])
def get_diseases():
    """Get list of available diseases"""
    try:
        diseases = ml_model.get_available_diseases()
        disease_list = [
            {'key': disease, 'name': disease.replace('_', ' ').title()}
            for disease in diseases
        ]
        return jsonify({'success': True, 'diseases': disease_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@ml_bp.route('/api/ml/symptoms/<disease>', methods=['GET'])
def get_disease_symptoms(disease):
    """Get symptoms for a specific disease"""
    try:
        symptoms = ml_model.get_disease_symptoms(disease.lower())
        symptom_list = [{'key': key, 'name': name} for key, name in symptoms.items()]
        return jsonify({
            'success': True,
            'disease': disease.replace('_', ' ').title(),
            'symptoms': symptom_list
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@ml_bp.route('/api/ml/symptoms', methods=['GET'])
def get_all_symptoms():
    """Get all unique symptoms across all diseases"""
    try:
        symptoms = ml_model.get_all_unique_symptoms()
        return jsonify({'success': True, 'symptoms': symptoms, 'count': len(symptoms)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@ml_bp.route('/api/ml/symptom-importance/<disease>', methods=['GET'])
def get_symptom_importance(disease):
    """Get symptom importance/weights for a disease"""
    try:
        importance = ml_model.get_symptom_importance(disease.lower())
        importance_list = [
            {'symptom': symptom, 'importance': round(weight * 100, 1)}
            for symptom, weight in importance.items()
        ]
        return jsonify({
            'success': True,
            'disease': disease.replace('_', ' ').title(),
            'symptom_importance': importance_list
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
 
@ml_bp.route('/api/ml/config', methods=['GET'])
def get_uncertainty_config():
    """
    Return the active uncertainty thresholds.
    Useful for admin dashboards and documentation.
    """
    return jsonify(uncertainty_handler.get_config()), 200
 
 
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
            'level': 'Low',
            'color': 'success',
            'description': 'Low probability of disease'
        }
    elif probability < 60:
        return {
            'level': 'Moderate',
            'color': 'warning',
            'description': 'Moderate probability - consider further testing'
        }
    elif probability < 85:
        return {
            'level': 'High',
            'color': 'danger',
            'description': 'High probability - immediate medical consultation recommended'
        }
    else:
        return {
            'level': 'Critical',
            'color': 'dark',
            'description': 'Critical risk level - urgent medical attention required'
        }
 