from flask import Blueprint, jsonify, request

from backend.utils.gemini_helper import generate_chat_response

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    """
    API endpoint to handle chatbot messages with conversation history.

    Expected JSON payload:
    {
        "messages": [
            {"role": "user", "text": "My name is Alex"},
            {"role": "model", "text": "Hello Alex! How can I help?"},
            {"role": "user", "text": "What is my name?"}
        ]
    }
    The last item is the current user message.
    All preceding items form the conversation history passed to the model.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        messages = data.get("messages")

        if not messages or not isinstance(messages, list):
            return jsonify({"error": "messages must be a non-empty list"}), 400

        # Get AI response with full conversation history
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
