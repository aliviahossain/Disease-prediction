from flask import Blueprint, jsonify, request
from backend.middleware import rate_limit

from backend.utils.gemini_helper import generate_chat_response

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/chat", methods=["POST"])
@rate_limit("default")
def chat():
    """
    API endpoint to handle chatbot messages.

    Expected JSON payload:
    {
        "messages": "History of chat"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        messages = data.get("messages")

        if not messages:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Get AI response
        ai_result = generate_chat_response(messages)

        if ai_result["success"]:
            return jsonify({"success": True, "response": ai_result["response"]}), 200
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": ai_result.get("error", "Unknown error"),
                        "response": ai_result.get("response", "Error occurred."),
                    }
                ),
                500,
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
