import os
import json
import re
import logging
from app.services.audit_service import historian
from app.services.agent_service import call_agent_api
from app.services.knowledge_service import knowledge_service
from app.services.sentinel_service import sentinel
from app.services.actuarial_service import actuarial
from app.services.guardrails_service import guardrails_service
from app.services.oracle_service import oracle
from app.services.debater_service import debater
from app.services.forensic_service import forensic

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
    4. RETIREMENT_SIMULATION: Requests for retirement projections, "will I have enough",
       Monte Carlo analysis, or "what if" scenario planning.
    5. MARKET_INTELLIGENCE: Questions about current stock prices, market trends,
       inflation, interest rates, or the economy.
    6. GENERAL: Greetings, thanks, or unrelated chit-chat.

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

    def dispatch(self, sanitized_message, user_profile, history, conversation_id, attachments=None):
        """
        Main entry point for agentic orchestration.
        Now includes a 'Behavioral Layer' (The Empath) and 'Multimodal Input' support.
        """
        logger.info("[Dispatcher] Starting dispatch | conv=%s msg_preview='%s'",
                    conversation_id, sanitized_message[:60])

        self._log_dispatch_start(sanitized_message, history, conversation_id)

        # 1. Market Awareness (The Oracle)
        # Injects real-time context into the advisor's world view
        market_data = oracle.get_market_context(conversation_id)
        
        # 1. Behavioral Analysis (The Empath)
        from app.services.empath_service import empath_agent
        sentiment = empath_agent.analyze(sanitized_message, conversation_id)
        
        # Add sentiment and market context for subsequent agents
        context_profile = (user_profile or {}).copy()
        context_profile["market_context"] = market_data.__dict__
        context_profile["behavioral_sentiment"] = {
            "score": sentiment.score,
            "bias": sentiment.bias,
            "suggested_tone": sentiment.suggested_tone
        }

        # 2. Conversational Guardrails (The Shield)
        # Filters jailbreaks, medical/legal queries, and off-topic chat
        guardrails_refusal = guardrails_service.check_query_sync(sanitized_message)
        if guardrails_refusal:
            logger.warning("[Dispatcher] Query BLOCKED by The Shield | conv=%s", conversation_id)
            historian.log_step(
                session_id=conversation_id,
                agent_name="Guardian",
                step_type="ACTION",
                content="Guardrails triggered: Refusing off-topic or unsafe query.",
                step_metadata={"refusal_preview": guardrails_refusal[:60]}
            )
            return guardrails_refusal

        # 3. Intent Classification
        intent_data = self._classify_intent(sanitized_message, context_profile, history)
        intent = intent_data.get("intent", "GENERAL")
        confidence = intent_data.get("confidence", 0.0)

        logger.info("[Dispatcher] Intent resolved: %s (confidence=%.2f) | conv=%s",
                    intent, confidence, conversation_id)

        self._log_intent_action(intent_data, conversation_id)

        return self._route(intent, intent_data, sanitized_message, context_profile, conversation_id)

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

        elif intent == "TRANSACTIONAL":
            logger.info("[Dispatcher] Routing to Sentinel → Executor | conv=%s", conversation_id)
            return self._handle_transaction(intent_data, user_profile, conversation_id)

        elif intent == "PORTFOLIO_ANALYSIS":
            logger.info("[Dispatcher] Routing to External Agent | intent=%s conv=%s",
                        intent, conversation_id)
            return self._handle_agent_call(intent_data, user_profile)

        elif intent == "RETIREMENT_SIMULATION":
            logger.info("[Dispatcher] Routing to Actuarial Agent | conv=%s", conversation_id)
            return self._handle_retirement_simulation(user_profile, conversation_id)

        elif intent == "MARKET_INTELLIGENCE":
            logger.info("[Dispatcher] Routing to Oracle Agent | conv=%s", conversation_id)
            return self._handle_market_query(message, conversation_id)

        else:
            logger.info("[Dispatcher] Intent=%s — falling through to general LLM | conv=%s",
                        intent, conversation_id)
            return None

    def _handle_market_query(self, message, conversation_id):
        """Oracle Agent: provides current economic and ticker data."""
        # Check if user mentioned a specific ticker
        tickers = re.findall(r"\b[A-Z]{3,5}\b", message)
        if tickers:
            quote = oracle.get_ticker_quote(tickers[0], conversation_id)
            return f"The current price for {tickers[0]} is £{quote['price']} ({quote['day_change']})."
        
        data = oracle.get_market_context(conversation_id)
        return (
            f"Current Market Context: The sentiment is currently {data.sentiment_score > 0.5 and 'Positive' or 'Neutral/Negative'}.\n"
            f"S&P 500: {data.indices['S&P 500']['price']} ({data.indices['S&P 500']['change']})\n"
            f"Key Indicator: US Inflation is at {data.economic_indicators['US Inflation (CPI)']}"
        )

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

    # -----------------------------------------------------------------------
    # Private — Sentinel → Executor (Pre-Trade Compliance Gate)
    # -----------------------------------------------------------------------

    def _handle_transaction(self, intent_data, user_profile, conversation_id):
        """
        Routes TRANSACTIONAL intents through the Sentinel compliance gate.
        """
        # 1. Forensic Anomaly Check (The Investigator)
        forensic_report = forensic.analyze_intent(intent_data, user_profile, conversation_id)
        
        # 2. Debater Gate (Ensemble Reasoning)
        # Directing high-stakes or anomalous trades to the multi-model ensemble
        if forensic_report["status"] == "RED" or intent_data.get("trade_value", 0) > 10000:
            logger.warning("[Dispatcher] High-Stakes Transaction detected -> Routing to Debater Agent | conv=%s", conversation_id)
            scenario_desc = f"User {user_profile.get('first_name')} wants to execute a {intent_data.get('sub_intent')} of {intent_data.get('asset')} valued at £{intent_data.get('trade_value')}. Forensic flags: {forensic_report['reasons']}"
            return debater.debate(scenario_desc, user_profile, conversation_id, domain=intent)

        # 3. Sentinel Compliance Check
        trade_intent = self._build_trade_intent(intent_data, user_profile)
        verdict = sentinel.pre_trade_check(
            trade_intent=trade_intent,
            user_profile=user_profile if user_profile else {},
            conversation_id=conversation_id,
        )

        return self._process_transaction_verdict(verdict, intent_data, user_profile, conversation_id)

    def _process_transaction_verdict(self, verdict, intent_data, user_profile, conversation_id):
        """Internal logic gate for Sentinel PASS/WARN/BLOCK outcomes."""
        if verdict.status == "BLOCK":
            logger.warning("[Dispatcher] Trade BLOCKED by Sentinel | reason='%s' conv=%s",
                           verdict.reason, conversation_id)
            return (
                f"⛔ **Trade Blocked** — This transaction cannot proceed.\n\n"
                f"**Reason**: {verdict.reason}\n\n"
                f"If you believe this is an error, please contact your financial advisor."
            )

        if verdict.status == "WARN":
            logger.info("[Dispatcher] Trade WARNING from Sentinel | reason='%s' conv=%s",
                        verdict.reason, conversation_id)
            # Proceed but attach advisory
            agent_response = self._handle_agent_call(intent_data, user_profile)
            return (
                f"⚠️ **Compliance Advisory**: {verdict.reason}\n\n"
                f"The trade is proceeding, but please review the advisory above.\n\n"
                f"{agent_response}"
            )

        # PASS
        logger.info("[Dispatcher] Sentinel PASS — proceeding to Executor | conv=%s", conversation_id)
        return self._handle_agent_call(intent_data, user_profile)

    def _build_trade_intent(self, intent_data, user_profile):
        """
        Extracts structured trade parameters from the Dispatcher's intent data
        and user profile for Sentinel evaluation.
        """
        return {
            "type": intent_data.get("sub_intent", "general_trade"),
            "value": intent_data.get("trade_value", 0),
            "risk_level": intent_data.get("risk_level", "moderate"),
            "asset": intent_data.get("asset", "unknown"),
        }

    # -----------------------------------------------------------------------
    # Private — Actuarial Agent (Retirement Simulation)
    # -----------------------------------------------------------------------

    def _handle_retirement_simulation(self, user_profile, conversation_id):
        """
        Actuarial Agent: runs a Monte Carlo retirement simulation.
        """
        logger.info("[Actuarial] Preparing retirement simulation | conv=%s", conversation_id)
        params = self._extract_simulation_params(user_profile)
        return self._execute_actuarial_simulation(params, conversation_id)

    def _execute_actuarial_simulation(self, params, conversation_id):
        """Executes the simulation engine and handles formatting/errors."""
        try:
            result = actuarial.simulate(
                **params,
                simulations=1000,
                conversation_id=conversation_id,
            )
            summary = actuarial.format_summary(result, params["retirement_age"])
            logger.info("[Actuarial] Simulation complete | success=%.1f%% conv=%s",
                        result.success_rate * 100, conversation_id)
            return summary

        except Exception as e:
            logger.error("[Actuarial] Simulation failed: %s | conv=%s",
                         e, conversation_id, exc_info=True)
            return (
                "I wasn't able to run a retirement projection at this time. "
                "Please ensure your financial profile is up to date and try again."
            )

    def _extract_simulation_params(self, user_profile):
        """
        Pulls simulation inputs from the user's profile, with sensible defaults.
        """
        profile = user_profile or {}
        financial = profile.get("financial_profile", {})
        personal = profile.get("personal_details", {})
        goals = profile.get("financial_goals", {})

        return {
            "initial_portfolio": financial.get("totalAssets", 50000),
            "monthly_contribution": financial.get("monthly_savings", 500),
            "annual_withdrawal": financial.get("annual_retirement_spending", 30000),
            "current_age": personal.get("age", 35),
            "retirement_age": goals.get("target_retirement_age", 67),
            "life_expectancy": goals.get("life_expectancy", 90),
        }


# Global singleton — imported by llm_service and routes
dispatcher = Orchestrator()

