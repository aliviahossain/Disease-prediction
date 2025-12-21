from flask import Blueprint, render_template, request, jsonify
from backend.models.ml_model import ml_model
from backend.utils.calculator import BayesCalculator

ml_bp = Blueprint('ml', __name__)

@ml_bp.route('/ml-prediction')
def ml_prediction_page():
    """Render the ML prediction page"""
    try:
        # Get available diseases and their symptoms
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
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        disease = data.get('disease')
        symptoms = data.get('symptoms', [])
        
        if not disease:
            return jsonify({'error': 'Disease not specified'}), 400
        
        if not symptoms or len(symptoms) == 0:
            return jsonify({'error': 'No symptoms provided'}), 400
        
        # Get ML prediction
        ml_prediction = ml_model.predict_disease_probability(disease, symptoms)
        
        # Calculate Bayesian probabilities
        calculator = BayesCalculator()
        bayesian_result = calculator.calculate_posterior(
            prior=ml_prediction['prior_probability'],
            likelihood=ml_prediction['likelihood'],
            false_positive_rate=0.05
        )
        
        # Combine results
        result = {
            'success': True,
            'disease': disease.replace('_', ' ').title(),
            'ml_prediction': {
                'raw_probability': round(ml_prediction['raw_probability'] * 100, 2),
                'confidence_score': round(ml_prediction['confidence_score'] * 100, 2),
                'symptoms_analyzed': ml_prediction['symptoms_matched']
            },
            'bayesian_analysis': {
                'prior': round(bayesian_result['prior'] * 100, 2),
                'likelihood': round(bayesian_result['likelihood'] * 100, 2),
                'posterior': round(bayesian_result['posterior'] * 100, 2),
                'false_positive_rate': round(bayesian_result['false_positive_rate'] * 100, 2)
            },
            'risk_assessment': get_risk_level(bayesian_result['posterior'] * 100)
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
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        symptoms = data.get('symptoms', [])
        
        if not symptoms or len(symptoms) == 0:
            return jsonify({'error': 'No symptoms provided'}), 400
        
        # Get predictions for all diseases
        predictions = ml_model.predict_multiple_diseases(symptoms)
        
        # Format results
        results = []
        calculator = BayesCalculator()
        
        for pred in predictions:
            bayesian = calculator.calculate_posterior(
                prior=pred['prior_probability'],
                likelihood=pred['likelihood'],
                false_positive_rate=0.05
            )
            
            results.append({
                'disease': pred['disease'].replace('_', ' ').title(),
                'probability': round(pred['raw_probability'] * 100, 2),
                'posterior': round(bayesian['posterior'] * 100, 2),
                'confidence': round(pred['confidence_score'] * 100, 2),
                'risk_level': get_risk_level(bayesian['posterior'] * 100)
            })
        
        return jsonify({
            'success': True,
            'predictions': results,
            'symptoms_count': len(symptoms)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@ml_bp.route('/api/ml/diseases', methods=['GET'])
def get_diseases():
    """Get list of available diseases"""
    try:
        diseases = ml_model.get_available_diseases()
        disease_list = [
            {
                'key': disease,
                'name': disease.replace('_', ' ').title()
            }
            for disease in diseases
        ]
        
        return jsonify({
            'success': True,
            'diseases': disease_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/api/ml/symptoms/<disease>', methods=['GET'])
def get_disease_symptoms(disease):
    """Get symptoms for a specific disease"""
    try:
        symptoms = ml_model.get_disease_symptoms(disease)
        
        symptom_list = [
            {
                'key': key,
                'name': name
            }
            for key, name in symptoms.items()
        ]
        
        return jsonify({
            'success': True,
            'disease': disease.replace('_', ' ').title(),
            'symptoms': symptom_list
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ml_bp.route('/api/ml/symptom-importance/<disease>', methods=['GET'])
def get_symptom_importance(disease):
    """Get symptom importance/weights for a disease"""
    try:
        importance = ml_model.get_symptom_importance(disease)
        
        importance_list = [
            {
                'symptom': symptom,
                'importance': round(weight * 100, 1)
            }
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
    else:
        return {
            'level': 'High',
            'color': 'danger',
            'description': 'High probability - immediate medical consultation recommended'
        }