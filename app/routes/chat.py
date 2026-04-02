from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.chat import Conversation, Message
from app.utils.auth import token_required
from app.services.llm_service import generate_ai_response, generate_suggested_questions

bp = Blueprint("chat", __name__)


@bp.route("/message", methods=["POST"])
@token_required
def send_message(current_user):
    data = request.get_json()

    if not data or not data.get("message"):
        return jsonify({"message": "No message provided"}), 400

    message_text = data["message"]
    conversation_id = data.get("conversation_id")

    # Get or create conversation
    if not conversation_id:
        conversation = Conversation(user_id=current_user.id)
        db.session.add(conversation)
        db.session.flush()  # Get the generated ID
        conversation_id = conversation.id
    else:
        conversation = Conversation.query.get(conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            return jsonify({"message": "Invalid conversation ID"}), 404

    # Save user message
    user_message = Message(conversation_id=conversation.id, content=message_text, type="user")
    db.session.add(user_message)

    # Get recent conversation history
    history = [
        msg.to_dict() for msg in conversation.messages.order_by(Message.timestamp).limit(20).all()
    ]

    # Exclude the message we just added from history calculation so we don't duplicate
    history = history[:-1] if history else []

    # Get AI response
    ai_response_text = generate_ai_response(
        message_text, user_profile=current_user.to_dict(), conversation_history=history
    )

    # Save bot message
    bot_message = Message(conversation_id=conversation.id, content=ai_response_text, type="bot")
    db.session.add(bot_message)

    db.session.commit()

    # Generate suggested questions
    suggested_questions = generate_suggested_questions(message_text, ai_response_text)

    # Dispatch continuous learning memory extraction in the background
    import threading
    from app.services.memory_service import summarize_into_facts

    threading.Thread(target=summarize_into_facts, args=(current_user.id, conversation.id)).start()

    return jsonify(
        {
            "message": {
                "id": bot_message.id,
                "content": ai_response_text,
                "type": "bot",
                "timestamp": bot_message.timestamp.isoformat(),
            },
            "conversation_id": conversation.id,
            "suggested_questions": suggested_questions,
        }
    )
