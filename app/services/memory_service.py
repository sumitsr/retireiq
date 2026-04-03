import json
import logging
from app import db, create_app
from app.models.chat import Conversation
from app.models.user_memory import UserMemory
from app.services.llm_service import call_openai_api, call_azure_openai_api_with_key
import os

logger = logging.getLogger(__name__)


def summarize_into_facts(user_id, conversation_id):
    """
    Called by a background thread. Reads the user's recent conversation and uses the LLM
    to extract permanent facts, preferences, or goals.
    """
    app = create_app()

    with app.app_context():
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation:
            return

        # Get last N messages
        recent_messages = conversation.messages.order_by("timestamp").all()[-10:]

        if not recent_messages:
            return

        chat_transcript = "\n".join(
            [f"{msg.type.upper()}: {msg.content}" for msg in recent_messages]
        )

        prompt = f"""
        Analyze the following conversation transcript between a retirement planning AI assistant and a user.
        Extract any permanent preferences, constraints, exclusions, or long-term financial goals the user explicitly states. 
        Ignore conversational filler or temporary issues.

        Output ONLY a JSON array of strings containing these distilled atomic facts.
        If no permanent facts were established, output an empty [] sequence.

        Transcript:
        {chat_transcript}
        """

        llm_config = {
            "provider": os.getenv("LLM_PROVIDER", "azure_openai"),
            "modelName": os.getenv("LLM_MODEL_NAME", "gpt-4o"),
            "temperature": 0.2,
        }

        try:
            ai_response = ""
            messages = [{"role": "system", "content": prompt}]

            if llm_config["provider"] == "openai":
                ai_response = call_openai_api(
                    messages, llm_config["modelName"], llm_config["temperature"]
                )
            else:
                # Use azure by default if not set
                ai_response = call_azure_openai_api_with_key(
                    messages, llm_config["modelName"], llm_config["temperature"]
                )

            if not ai_response:
                return

            # Clean JSON formatting issues
            ai_response = ai_response.strip().replace("```json", "").replace("```", "")

            facts = json.loads(ai_response)

            if isinstance(facts, list):
                for fact in facts:
                    # Check if essentially the exact same fact is already remembered (basic deduplication)
                    existing = UserMemory.query.filter_by(user_id=user_id, fact_text=fact).first()
                    if not existing:
                        memory = UserMemory(
                            user_id=user_id, fact_text=fact, category="learned_fact"
                        )
                        db.session.add(memory)
                        logger.info(f"Learned new memory for {user_id}: {fact}")

                db.session.commit()

        except Exception as e:
            logger.error(f"Failed to generate memories: {e}")
            db.session.rollback()
