from flask import Blueprint, request, jsonify
from backend.utils.gemini_helper import generate_chat_response

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    API endpoint to handle chatbot messages.
    
    Expected JSON payload:
    {
        "message": "User's question here"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
            
        # Get AI response
        ai_result = generate_chat_response(message)
        
        if ai_result['success']:
            return jsonify({
                'success': True,
                'response': ai_result['response']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': ai_result.get('error', 'Unknown error'),
                'response': ai_result.get('response', 'Error occurred.')
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
