import logging
import threading
from flask import Blueprint, request, jsonify, Response, current_app, stream_with_context
from app import db
from app.models.chat import Conversation, Message
from app.utils.auth import token_required
from app.services.llm_service import generate_ai_response, generate_suggested_questions
from app.services.sse_service import sse_service

logger = logging.getLogger(__name__)
bp = Blueprint("chat", __name__)


# ---------------------------------------------------------------------------
# Route: POST /message
# ---------------------------------------------------------------------------

@bp.route("/message", methods=["POST"])
@token_required
def send_message(current_user):
    """
    Accepts a user message, optionally streams the agent's reasoning via SSE.

    - stream=true  → returns 202 immediately; client polls GET /stream/<id>
    - stream=false → waits for the thread to finish (synchronous, legacy mode)
    """
    data = request.get_json()
    if not data or not data.get("message"):
        logger.warning("[Chat] Missing 'message' in request | user=%s", current_user.id)
        return jsonify({"message": "No message provided"}), 400

    message_text = data["message"]
    conversation_id = data.get("conversation_id")
    is_streaming = data.get("stream", False)
    attachments = data.get("attachments", None) # List of base64 or URIs

    logger.info("[Chat] Incoming message | user=%s conv=%s stream=%s multimodal=%s",
                current_user.id, conversation_id, is_streaming, bool(attachments))

    # Resolve or create the conversation
    conversation, error_response = _resolve_conversation(current_user, conversation_id)
    if error_response:
        return error_response

    # Persist the user's message
    _save_message(conversation.id, message_text, "user")

    # Build history (excluding the message we just saved)
    history = _load_history(conversation)

    # Launch background agent thread
    thread = _start_agent_thread(current_user, conversation, message_text, history)

    if is_streaming:
        logger.info("[Chat] Streaming mode — returning 202 | conv=%s", conversation.id)
        return jsonify({"status": "accepted", "conversation_id": conversation.id}), 202

    # Synchronous (legacy) mode — wait for thread completion
    logger.info("[Chat] Synchronous mode — waiting for agent thread | conv=%s", conversation.id)
    thread.join()
    return _build_sync_response(conversation.id)


# ---------------------------------------------------------------------------
# Route: GET /stream/<conversation_id>
# ---------------------------------------------------------------------------

@bp.route("/stream/<int:conversation_id>", methods=["GET"])
@token_required
def stream_conversation(current_user, conversation_id):
    """
    Real-time SSE endpoint for observing agentic reasoning and final responses.
    The client should connect here *before* or immediately after POST /message.
    """
    logger.info("[Chat] SSE subscription requested | user=%s conv=%s",
                current_user.id, conversation_id)

    conversation = db.session.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        logger.warning("[Chat] Invalid conversation ID | user=%s conv=%s",
                       current_user.id, conversation_id)
        return jsonify({"message": "Invalid conversation ID"}), 404

    return Response(
        stream_with_context(sse_service.subscribe(conversation_id)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Private — Conversation helpers
# ---------------------------------------------------------------------------

def _resolve_conversation(current_user, conversation_id):
    """
    Returns (Conversation, None) on success, or (None, error_response) on failure.
    Creates a new conversation if conversation_id is not provided.
    """
    if not conversation_id:
        conversation = Conversation(user_id=current_user.id)
        db.session.add(conversation)
        db.session.flush()
        logger.info("[Chat] New conversation created | conv=%s user=%s",
                    conversation.id, current_user.id)
        return conversation, None

    conversation = db.session.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        logger.warning("[Chat] Conversation not found or unauthorised | conv=%s user=%s",
                       conversation_id, current_user.id)
        return None, (jsonify({"message": "Invalid conversation ID"}), 404)

    return conversation, None


def _save_message(conversation_id, content, msg_type):
    """Persists a single message and commits the session."""
    message = Message(conversation_id=conversation_id, content=content, type=msg_type)
    db.session.add(message)
    db.session.commit()
    logger.debug("[Chat] Saved %s message | conv=%s", msg_type, conversation_id)
    return message


def _load_history(conversation, limit=20):
    """
    Loads the N most recent messages, excluding the last one
    (which is the message the user just sent).
    """
    messages = conversation.messages.order_by(Message.timestamp).limit(limit).all()
    history = [msg.to_dict() for msg in messages][:-1]
    logger.debug("[Chat] Loaded %d history messages | conv=%s", len(history), conversation.id)
    return history


def _build_sync_response(conversation_id):
    """Builds the JSON response for synchronous (non-streaming) callers."""
    latest = (
        Message.query
        .filter_by(conversation_id=conversation_id, type="bot")
        .order_by(Message.timestamp.desc())
        .first()
    )
    return jsonify({
        "message": {
            "id": latest.id if latest else None,
            "content": latest.content if latest else "Processing failed or timed out",
            "type": "bot",
            "timestamp": latest.timestamp.isoformat() if latest else None,
        },
        "conversation_id": conversation_id,
    })


# ---------------------------------------------------------------------------
# Private — Background task
# ---------------------------------------------------------------------------

def _start_agent_thread(current_user, conversation, message_text, history, attachments=None):
    """Spawns the background thread that runs the full agentic pipeline."""
    thread = threading.Thread(
        target=_run_agent_task,
        args=(
            current_app.app_context(),
            current_user.to_dict(),
            message_text,
            history,
            conversation.id,
            attachments
        ),
        daemon=True,
    )
    thread.start()
    logger.debug("[Chat] Agent thread started | conv=%s", conversation.id)
    return thread


def _run_agent_task(app_context, user_dict, msg_text, history, conv_id, attachments):
    """
    Background thread target.  Runs inside the Flask app context.
    """
    with app_context:
        logger.info("[AgentTask] Starting background task | conv=%s", conv_id)
        try:
            ai_response = _invoke_agent(user_dict, msg_text, history, conv_id, attachments)
            bot_message = _persist_bot_response(conv_id, ai_response)
            _broadcast_final_response(conv_id, ai_response, bot_message.id)
            _trigger_memory_summarization(user_dict, conv_id)
        except Exception as e:
            logger.error("[AgentTask] Unhandled exception in background task: %s | conv=%s",
                         e, conv_id, exc_info=True)
            sse_service.publish(session_id=conv_id, event="error", data={"message": str(e)})


def _invoke_agent(user_dict, msg_text, history, conv_id, attachments):
    """Calls the full agentic pipeline and returns the final response string."""
    logger.info("[AgentTask] Invoking agentic pipeline | conv=%s", conv_id)
    from app.services.llm_service import generate_ai_response
    response = generate_ai_response(
        msg_text,
        user_profile=user_dict,
        conversation_history=history,
        conversation_id=conv_id,
        attachments=attachments
    )
    logger.info("[AgentTask] Agentic pipeline complete | conv=%s", conv_id)
    return response


def _persist_bot_response(conv_id, response_text):
    """Writes the bot's final answer to the database and returns the Message object."""
    bot_message = Message(conversation_id=conv_id, content=response_text, type="bot")
    db.session.add(bot_message)
    db.session.commit()
    logger.debug("[AgentTask] Bot message persisted | id=%s conv=%s", bot_message.id, conv_id)
    return bot_message


def _broadcast_final_response(conv_id, response_text, message_id):
    """Broadcasts the final_response SSE event to all connected clients."""
    sse_service.publish(
        session_id=conv_id,
        event="final_response",
        data={"content": response_text, "message_id": message_id},
    )
    logger.info("[AgentTask] Final SSE response broadcast | conv=%s msg_id=%s", conv_id, message_id)


def _trigger_memory_summarization(user_dict, conv_id):
    """Fires the background memory summarisation task (non-blocking)."""
    from app.services.memory_service import summarize_into_facts
    user_id = user_dict.get("id")
    logger.debug("[AgentTask] Triggering memory summarization | user=%s conv=%s", user_id, conv_id)
    summarize_into_facts(user_id, conv_id)
