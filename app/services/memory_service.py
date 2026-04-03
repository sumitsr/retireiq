import json
import logging
from app import db, create_app
from app.models.chat import Conversation
from app.models.user_memory import UserMemory
from app.services.llm_service import call_openai_api, call_azure_openai_api_with_key
import os

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarize_into_facts(user_id, conversation_id):
    """
    Background task entry point.

    Reads the most recent messages from a conversation, asks the LLM to extract
    permanent preferences and goals, and persists deduplicated facts to UserMemory.
    """
    logger.info("[MemoryService] Starting fact summarization | user=%s conv=%s",
                user_id, conversation_id)

    app = create_app()
    with app.app_context():
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation:
            logger.warning("[MemoryService] Conversation %s not found; skipping.", conversation_id)
            return

        recent_messages = _get_recent_messages(conversation)
        if not recent_messages:
            logger.info("[MemoryService] No recent messages found | conv=%s", conversation_id)
            return

        transcript = _build_transcript(recent_messages)
        facts = _call_memory_llm(transcript, conversation_id)

        if facts:
            _persist_facts(user_id, facts, conversation_id)
        else:
            logger.info("[MemoryService] No new facts extracted | conv=%s", conversation_id)


# ---------------------------------------------------------------------------
# Private — Data helpers
# ---------------------------------------------------------------------------

def _get_recent_messages(conversation, limit=10):
    """Fetches the N most recent messages for the conversation."""
    messages = conversation.messages.order_by("timestamp").all()[-limit:]
    logger.debug("[MemoryService] Fetched %d recent messages | conv=%s",
                 len(messages), conversation.id)
    return messages


def _build_transcript(messages):
    """Formats a list of Message objects into a readable plain-text transcript."""
    transcript = "\n".join(
        [f"{msg.type.upper()}: {msg.content}" for msg in messages]
    )
    logger.debug("[MemoryService] Built transcript (%d chars).", len(transcript))
    return transcript


# ---------------------------------------------------------------------------
# Private — LLM interaction
# ---------------------------------------------------------------------------

def _build_memory_prompt(transcript):
    """Returns the fact-extraction prompt for the LLM."""
    return f"""
Analyze the following conversation transcript between a retirement planning AI assistant and a user.
Extract any permanent preferences, constraints, exclusions, or long-term financial goals the user
explicitly states. Ignore conversational filler or temporary issues.

Output ONLY a JSON array of strings containing these distilled atomic facts.
If no permanent facts were established, output an empty [] array.

Transcript:
{transcript}
"""


def _call_memory_llm(transcript, conversation_id):
    """
    Calls the configured LLM provider to extract facts from the transcript.
    Returns a list of fact strings, or an empty list on failure.
    """
    provider = os.getenv("LLM_PROVIDER", "azure_openai")
    model = os.getenv("LLM_MODEL_NAME", "gpt-4o")
    temperature = 0.2  # Low temperature for structured extraction

    logger.info("[MemoryService] Calling LLM for fact extraction | provider=%s model=%s conv=%s",
                provider, model, conversation_id)

    prompt = _build_memory_prompt(transcript)
    messages = [{"role": "system", "content": prompt}]

    try:
        if provider == "openai":
            raw = call_openai_api(messages, model, temperature)
        else:
            raw = call_azure_openai_api_with_key(messages, model, temperature)

        return _parse_facts(raw, conversation_id)

    except Exception as e:
        logger.error("[MemoryService] LLM call failed: %s | conv=%s", e, conversation_id, exc_info=True)
        return []


def _parse_facts(raw_response, conversation_id):
    """
    Cleans the raw LLM response and parses it as a JSON list of strings.
    Returns the list on success, or an empty list on any parse failure.
    """
    if not raw_response:
        logger.warning("[MemoryService] Empty LLM response | conv=%s", conversation_id)
        return []

    cleaned = raw_response.strip().replace("```json", "").replace("```", "")
    logger.debug("[MemoryService] Cleaned LLM response: %s", cleaned[:120])

    try:
        facts = json.loads(cleaned)
        if isinstance(facts, list):
            logger.info("[MemoryService] Extracted %d fact(s) | conv=%s", len(facts), conversation_id)
            return facts
        else:
            logger.warning("[MemoryService] LLM returned non-list JSON; ignoring. | conv=%s", conversation_id)
    except json.JSONDecodeError as e:
        logger.warning("[MemoryService] Failed to parse facts JSON: %s | conv=%s", e, conversation_id)

    return []


# ---------------------------------------------------------------------------
# Private — Persistence
# ---------------------------------------------------------------------------

def _persist_facts(user_id, facts, conversation_id):
    """
    Writes new, deduplicated facts to UserMemory.
    Rolls back the session on any database error.
    """
    logger.info("[MemoryService] Persisting facts | user=%s count=%d conv=%s",
                user_id, len(facts), conversation_id)
    new_count = 0
    try:
        for fact in facts:
            if _is_new_fact(user_id, fact):
                memory = UserMemory(user_id=user_id, fact_text=fact, category="learned_fact")
                db.session.add(memory)
                new_count += 1
                logger.debug("[MemoryService] New fact learned: '%s'", fact[:80])

        db.session.commit()
        logger.info("[MemoryService] Committed %d new fact(s) | user=%s", new_count, user_id)

    except Exception as e:
        logger.error("[MemoryService] DB commit failed: %s | user=%s", e, user_id, exc_info=True)
        db.session.rollback()


def _is_new_fact(user_id, fact_text):
    """Returns True if this exact fact text doesn't already exist in UserMemory."""
    existing = UserMemory.query.filter_by(user_id=user_id, fact_text=fact_text).first()
    return existing is None
