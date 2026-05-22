from flask import Blueprint, request, jsonify

from backend.middleware.error_handler import (
    ValidationError,
    error_response,
    handle_errors,
    validate_json_request,
)
from backend.utils.gemini_helper import generate_chat_response

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/chat', methods=['POST'])
@handle_errors
@validate_json_request
def chat():
    """
    API endpoint to handle chatbot messages.

    Expected JSON payload:
    {
        "message": "User's question here"
    }
    """
    data = request.get_json()

    message = data.get('message')
    if not message or not str(message).strip():
        raise ValidationError("Message cannot be empty")

    ai_result = generate_chat_response(message)

    if ai_result['success']:
        return jsonify({
            'success': True,
            'response': ai_result['response']
        }), 200

    return error_response(
        ai_result.get('error', 'Chat service unavailable'),
        status_code=502,
        response=ai_result.get(
            'response',
            'Unable to generate a response at this time.'
        )
    )
