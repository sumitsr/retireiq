import os
import json
import re
import logging
from app.services.audit_service import historian
from app.services.agent_service import call_agent_api
from app.services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    The Multi-Agent Dispatcher (The Router).
    Classifies user intent and delegates to the appropriate specialist agent.
    """

    # -----------------------------------------------------------------------
    # Constants
    # -----------------------------------------------------------------------

    CLASSIFICATION_SYSTEM_PROMPT = """
    You are the RetireIQ Dispatcher Agent. Your ONLY job is to classify the user's
    intent into exactly one of these categories:

    1. KNOWLEDGE_BASE: Questions about retirement policies, 401k rules, or general
       financial education.
    2. PORTFOLIO_ANALYSIS: Requests for account balances, investment performance,
       or goal tracking.
    3. TRANSACTIONAL: Requests to buy/sell assets, register accounts, or change
       personal info.
    4. GENERAL: Greetings, thanks, or unrelated chit-chat.

    Output ONLY a JSON object with no extra text:
    {
        "intent": "CATEGORY",
        "sub_intent": "brief description",
        "confidence": 0.0-1.0
    }
    """

    FALLBACK_INTENT = {"intent": "GENERAL", "sub_intent": "fallback", "confidence": 0.0}

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def dispatch(self, sanitized_message, user_profile, history, conversation_id):
        """
        Main entry point for agentic orchestration.

        Returns:
            A response string from a specialist agent, or None to signal that
            the general LLM fallback should be used.
        """
        logger.info("[Dispatcher] Starting dispatch | conv=%s msg_preview='%s'",
                    conversation_id, sanitized_message[:60])

        self._log_dispatch_start(sanitized_message, history, conversation_id)

        intent_data = self._classify_intent(sanitized_message, user_profile, history)
        intent = intent_data.get("intent", "GENERAL")
        confidence = intent_data.get("confidence", 0.0)

        logger.info("[Dispatcher] Intent resolved: %s (confidence=%.2f) | conv=%s",
                    intent, confidence, conversation_id)

        self._log_intent_action(intent_data, conversation_id)

        return self._route(intent, intent_data, sanitized_message, user_profile, conversation_id)

    # -----------------------------------------------------------------------
    # Private — Audit helpers
    # -----------------------------------------------------------------------

    def _log_dispatch_start(self, message, history, conversation_id):
        """Logs the initial THOUGHT step to the Historian."""
        historian.log_step(
            session_id=conversation_id,
            agent_name="Dispatcher",
            step_type="THOUGHT",
            content=f"Resolving intent for: '{message[:60]}...'",
            step_metadata={"history_length": len(history) if history else 0},
        )

    def _log_intent_action(self, intent_data, conversation_id):
        """Logs the resolved intent as an ACTION step to the Historian."""
        historian.log_step(
            session_id=conversation_id,
            agent_name="Dispatcher",
            step_type="ACTION",
            content=f"Intent resolved: {intent_data.get('intent')}",
            step_metadata=intent_data,
        )

    # -----------------------------------------------------------------------
    # Private — Intent classification
    # -----------------------------------------------------------------------

    def _classify_intent(self, message, profile, history):
        """
        Uses a fast, deterministic LLM call (T=0.0) to classify intent.
        Falls back to GENERAL if classification fails.
        """
        from app.services.llm_service import (
            call_openai_api, call_azure_openai_api_with_key,
            call_ollama_api, prepare_openai_messages,
        )

        provider = os.getenv("LLM_PROVIDER", "azure_openai")
        model = os.getenv("LLM_MODEL_NAME", "gpt-4o")
        logger.debug("[Dispatcher] Classifying intent | provider=%s model=%s", provider, model)

        messages = prepare_openai_messages(self.CLASSIFICATION_SYSTEM_PROMPT, history, message)

        raw_response = self._call_classification_llm(
            provider, messages, model, call_openai_api,
            call_azure_openai_api_with_key, call_ollama_api,
        )

        return self._parse_intent_response(raw_response)

    def _call_classification_llm(self, provider, messages, model,
                                  call_openai, call_azure, call_ollama):
        """
        Delegates the raw LLM call to the correct provider adapter.
        Temperature is always 0.0 for deterministic classification.
        """
        try:
            if provider == "openai":
                return call_openai(messages, model, 0.0)
            elif provider == "azure_openai":
                return call_azure(messages, model, 0.0)
            else:
                # Vertex AI and Ollama both fall back to Ollama for classification
                return call_ollama(messages, model, 0.0)
        except Exception as e:
            logger.error("[Dispatcher] LLM classification call failed: %s", e, exc_info=True)
            return None

    def _parse_intent_response(self, raw_response):
        """
        Extracts and validates the JSON intent object from the raw LLM response.
        Returns FALLBACK_INTENT on any parse failure.
        """
        if not raw_response:
            logger.warning("[Dispatcher] Empty LLM response; using GENERAL fallback.")
            return self.FALLBACK_INTENT

        try:
            match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if match:
                intent_data = json.loads(match.group())
                logger.debug("[Dispatcher] Parsed intent data: %s", intent_data)
                return intent_data
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("[Dispatcher] Failed to parse intent JSON: %s | raw='%s'", e, raw_response[:100])

        return self.FALLBACK_INTENT

    # -----------------------------------------------------------------------
    # Private — Routing
    # -----------------------------------------------------------------------

    def _route(self, intent, intent_data, message, user_profile, conversation_id):
        """Dispatches to the correct specialist handler based on classified intent."""
        if intent == "KNOWLEDGE_BASE":
            logger.info("[Dispatcher] Routing to Scholar Agent | conv=%s", conversation_id)
            return self._handle_knowledge_query(message, conversation_id)

        elif intent in ("TRANSACTIONAL", "PORTFOLIO_ANALYSIS"):
            logger.info("[Dispatcher] Routing to External Agent | intent=%s conv=%s",
                        intent, conversation_id)
            return self._handle_agent_call(intent_data, user_profile)

        else:
            logger.info("[Dispatcher] Intent=%s — falling through to general LLM | conv=%s",
                        intent, conversation_id)
            return None

    def _handle_agent_call(self, intent_data, user_profile):
        """Delegates transactional or portfolio requests to the external Agent API."""
        user_id = user_profile.get("id", "") if user_profile else ""
        logger.debug("[Executor] Calling agent_api | user_id=%s intent=%s",
                     user_id, intent_data.get("intent"))
        return call_agent_api(intent_data, user_id)

    # -----------------------------------------------------------------------
    # Private — Scholar Agent (Knowledge / RAG)
    # -----------------------------------------------------------------------

    def _handle_knowledge_query(self, message, conversation_id):
        """
        Scholar Agent: performs semantic retrieval and returns a grounded response.
        """
        logger.info("[Scholar] Searching knowledge base | conv=%s", conversation_id)
        historian.log_step(
            session_id=conversation_id,
            agent_name="Scholar",
            step_type="THOUGHT",
            content="Searching knowledge base for relevant policy context.",
            step_metadata={"query_preview": message[:80]},
        )

        context_chunks = self._retrieve_context(message, conversation_id)

        if not context_chunks:
            logger.warning("[Scholar] No relevant chunks found | conv=%s", conversation_id)
            return (
                "I couldn't find any specific information in our policies regarding that. "
                "Let me try as a general assistant."
            )

        return self._build_grounded_response(context_chunks, conversation_id)

    def _retrieve_context(self, message, conversation_id):
        """Runs pgvector / Vertex semantic search and logs the OBSERVATION step."""
        try:
            context_chunks = knowledge_service.search_knowledge(message)
        except Exception as e:
            logger.error("[Scholar] Knowledge search failed: %s | conv=%s", e, conversation_id, exc_info=True)
            context_chunks = []

        historian.log_step(
            session_id=conversation_id,
            agent_name="Scholar",
            step_type="OBSERVATION",
            content=f"Found {len(context_chunks)} relevant policy snippets.",
            step_metadata={"chunk_ids": [c.id for c in context_chunks]},
        )
        logger.debug("[Scholar] Retrieved %d chunks | conv=%s", len(context_chunks), conversation_id)
        return context_chunks

    def _build_grounded_response(self, context_chunks, conversation_id):
        """Assembles the final grounded response from retrieved context."""
        context_text = "\n".join([c.content for c in context_chunks])
        response = f"Based on our documents: {context_text}"
        logger.info("[Scholar] Grounded response built from %d chunks | conv=%s",
                    len(context_chunks), conversation_id)
        return response


# Global singleton — imported by llm_service and routes
dispatcher = Orchestrator()
