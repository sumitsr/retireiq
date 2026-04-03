import os
import json
import re
import logging
import requests
from app.services.agent_service import call_agent_api
from app.services.audit_service import historian
from app.services.orchestrator import dispatcher

logger = logging.getLogger(__name__)

try:
    import openai
except ImportError:
    pass

try:
    import anthropic
except ImportError:
    pass

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part, Content, GenerationConfig
    from vertexai.preview import caching
    from vertexai.language_models import TextEmbeddingModel
except ImportError:
    vertexai = None
    GenerativeModel = Part = Content = GenerationConfig = caching = TextEmbeddingModel = None

from app.utils.pii_sanitizer import sanitizer


# ---------------------------------------------------------------------------
# Prompt Builders
# ---------------------------------------------------------------------------

def build_system_prompt(user_profile_string=""):
    """Builds the base RetireIQ advisor system prompt from an anonymised profile."""
    try:
        parsed = json.loads(user_profile_string)
    except Exception:
        logger.debug("Could not parse user_profile_string; defaulting to empty profile.")
        parsed = {}

    memories = parsed.get("memories", [])
    tone_instruction = _apply_behavioral_tone(parsed)

    return f"""
    As RetireIQ, a retirement agent chatbot with access to the customer's structured personal and
    financial data in JSON format, begin a short, personalized conversation to guide the customer
    toward the sub-intent "Choose retirement investments." First, extract the customer's first name
    from the field personal_details.first_name and use it naturally to address them throughout the
    interaction. Acknowledge their current financial stage without repeating known details.{tone_instruction}
    Ask if they're currently more focused on growing long-term retirement savings or keeping flexibility for
    short-term needs. Based on their response, follow up to understand whether they prefer a hands-on
    investment style or an automated, guided approach. If needed, ask if they have specific
    preferences or exclusions (e.g., ESG, sectors to avoid). Keep the conversation friendly and
    concise, ask only relevant questions (up to five), and stop once enough information is gathered
    to recommend suitable retirement investment options tailored to their goals and preferences.

    Once intent and sub-intent are known, output your understanding in the following structured JSON
    format only and don't add any other text anywhere in response:
    {{
        "intent": "<detected primary intent>",
        "sub_intent": "<detected sub-intent details>",
        "summary": "<short natural-language summary of what the customer wants>"
    }}

    Historical Context / Permanent Memories:
    {json.dumps(memories)}

    User Profile Data: {user_profile_string}
    """


def _apply_behavioral_tone(profile):
    """
    Step 1b — Behavioral Logic: Returns the persona adjustment instruction
    based on the Empath's sentiment analysis.
    """
    sentiment = profile.get("behavioral_sentiment", {})
    bias = sentiment.get("bias", "NEUTRAL")
    
    if bias == "PANIC":
        return "\n    CRITICAL: The user is showing signs of anxiety or PANIC. Use an extremely CALMING, REASSURING, and empathetic tone. Provide objective data to ground their fears."
    elif bias == "FOMO":
        return "\n    CRITICAL: The user is showing signs of FOMO or over-excitement. Use a CAUTIONARY, PRUDENT tone. Remind them of long-term risks and diversification."
    
    return ""


def prepare_openai_messages(system_prompt, conversation_history, message):
    """Assembles the messages list in OpenAI chat-completion format."""
    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        for msg in conversation_history:
            role = "user" if msg["type"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})

    messages.append({"role": "user", "content": message})
    logger.debug("Prepared %d messages for OpenAI-format call.", len(messages))
    return messages


def prepare_azure_openai_messages(system_prompt, conversation_history, message):
    """Alias for prepare_openai_messages (Azure uses the same format)."""
    return prepare_openai_messages(system_prompt, conversation_history, message)


# ---------------------------------------------------------------------------
# LLM Provider Adapters
# ---------------------------------------------------------------------------

def call_openai_api(messages, model, temperature):
    """Calls the OpenAI Chat Completions API and returns the response text."""
    logger.info("Calling OpenAI API | model=%s temperature=%s", model, temperature)
    try:
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        if not client.api_key:
            logger.warning("OPENAI_API_KEY is not configured.")
            return "I'm sorry, the OpenAI API key is not configured correctly."

        response = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature, max_tokens=500
        )
        content = response.choices[0].message.content
        logger.debug("OpenAI response received (first 80 chars): %s", content[:80])
        return content
    except Exception as e:
        logger.error("OpenAI API call failed: %s", e, exc_info=True)
        return f"I'm sorry, I encountered an error processing your request: {e}"


def call_ollama_api(messages, model, temperature):
    """Calls a locally-running Ollama instance and returns the response text."""
    base_url = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
    url = f"{base_url}/api/chat"
    logger.info("Calling Ollama API | url=%s model=%s", url, model)

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "")
        logger.debug("Ollama response received (first 80 chars): %s", content[:80])
        return content
    except Exception as e:
        logger.error("Ollama API call failed: %s", e, exc_info=True)
        return f"I'm sorry, I encountered an error with the local Ollama service: {e}"


def call_vertex_ai_api(prompt, model_name="gemini-1.5-pro", temperature=0.7, attachments=None):
    """
    Calls Google Cloud Vertex AI (Gemini 1.5) and returns the response text.
    Supports multimodal inputs if attachments (list of base64 data) are provided.
    """
    if not vertexai:
        logger.warning("Vertex AI SDK not installed. Returning fallback.")
        return "Vertex AI SDK not installed. Please check requirements.txt."

    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_REGION", "us-central1")
    logger.info("Calling Vertex AI | model=%s multimodal=%s", model_name, bool(attachments))

    try:
        vertexai.init(project=project_id, location=location)
        model = GenerativeModel(model_name)
        config = GenerationConfig(temperature=temperature, max_output_tokens=2048)
        
        # Assemble multimodal content
        contents = [prompt]
        if attachments:
            for att in attachments:
                if isinstance(att, str): # Assume base64 or URI
                    if att.startswith("gs://"):
                        contents.append(Part.from_uri(att, mime_type="application/pdf"))
                    else:
                        contents.append(Part.from_data(att, mime_type="image/jpeg"))

        response = model.generate_content(contents, generation_config=config)
        return response.text
    except Exception as e:
        logger.error("Vertex AI call failed: %s", e)
        return f"Vertex AI Error: {str(e)}"


def call_azure_openai_api_with_key(messages, model, temperature=0.7, max_tokens=500):
    """Calls Azure-hosted OpenAI via the legacy ChatCompletion API."""
    logger.info("Calling Azure OpenAI | model=%s temperature=%s", model, temperature)
    try:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")

        if not api_key or not api_base:
            logger.warning("Azure OpenAI credentials are not fully configured.")
            return "I'm sorry, the Azure OpenAI API key or endpoint is not configured correctly."

        openai.api_type = "azure"
        openai.api_key = api_key
        openai.api_base = api_base
        openai.api_version = api_version

        response = openai.ChatCompletion.create(
            engine=model, messages=messages, temperature=temperature, max_tokens=max_tokens
        )
        content = response["choices"][0]["message"]["content"]
        logger.debug("Azure OpenAI response received (first 80 chars): %s", content[:80])
        return content
    except Exception as e:
        logger.error("Azure OpenAI API call failed: %s", e, exc_info=True)
        return f"I'm sorry, I encountered an error processing your request: {e}"


# ---------------------------------------------------------------------------
# LLM Provider Router
# ---------------------------------------------------------------------------

def _resolve_llm_config():
    """Resolves the active LLM provider, model, and temperature from environment."""
    provider = os.getenv("LLM_PROVIDER", "azure_openai")
    default_model = "gemini-1.5-pro" if provider == "vertex_ai" else "gpt-4o"
    return {
        "provider": provider,
        "modelName": os.getenv("LLM_MODEL_NAME") or default_model,
        "temperature": float(os.getenv("LLM_TEMPERATURE", 0.7)),
    }


def _call_llm_provider(
    provider, model, temperature, system_prompt, history, sanitized_message, 
    attachments=None
):
    """Routes to the correct LLM provider adapter. Supports multimodal for Vertex AI."""
    logger.info("Routing to LLM provider: %s | multimodal=%s", provider, bool(attachments))

    if provider == "openai":
        messages = prepare_openai_messages(system_prompt, history, sanitized_message)
        return call_openai_api(messages, model, temperature)

    elif provider == "azure_openai":
        messages = prepare_azure_openai_messages(system_prompt, history, sanitized_message)
        return call_azure_openai_api_with_key(messages, model, temperature)

    elif provider == "vertex_ai":
        full_prompt = f"{system_prompt}\n\nUser: {sanitized_message}"
        return call_vertex_ai_api(full_prompt, model, temperature, attachments=attachments)

    elif provider == "ollama":
        messages = prepare_openai_messages(system_prompt, history, sanitized_message)
        return call_ollama_api(messages, model, temperature)

    else:
        logger.error("Unknown LLM provider configured: '%s'", provider)
        return None


def _run_pii_scrub(message, user_profile, conversation_id):
    """
    Step 1 — Guardian Agent: Anonymises the incoming message and profile.
    Returns (sanitized_message, anonymized_profile_string).
    """
    logger.debug("[Guardian] Starting PII anonymisation | conv=%s", conversation_id)
    historian.log_step(
        session_id=conversation_id,
        agent_name="Guardian",
        step_type="THOUGHT",
        content="Initializing PII sanitization for user profile and message.",
    )

    sanitizer.clear_mapping()
    anonymized_profile = sanitizer.sanitize_profile_to_string(user_profile if user_profile else {})
    sanitized_message, message_mapping = sanitizer.sanitize_text(message)
    sanitizer.mapping.update(message_mapping)

    logger.info(
        "[Guardian] Anonymisation complete | entities_masked=%d conv=%s",
        len(message_mapping),
        conversation_id,
    )
    historian.log_step(
        session_id=conversation_id,
        agent_name="Guardian",
        step_type="ACTION",
        content=f"Anonymization complete. {len(message_mapping)} entities masked.",
    )
    return sanitized_message, anonymized_profile


def _run_dispatch(sanitized_message, user_profile, history, conversation_id):
    """
    Step 2 — Dispatcher Agent: Routes the message to a specialist agent.
    Returns the agent response string, or None to fall through to general LLM.
    """
    logger.info("[Dispatcher] Dispatching message | conv=%s", conversation_id)
    agent_response = dispatcher.dispatch(sanitized_message, user_profile, history, conversation_id)

    if agent_response:
        logger.info("[Dispatcher] Specialist agent responded | conv=%s", conversation_id)
    else:
        logger.info("[Dispatcher] No specialist matched; falling through to general LLM | conv=%s", conversation_id)

    return agent_response


def _run_general_llm(
    provider, model, temperature, anonymized_profile, history, sanitized_message, 
    attachments=None
):
    """
    Step 3 — General LLM Fallback: Handles small-talk and non-domain queries.
    Returns the raw (still anonymised) response string.
    """
    logger.info("[General LLM] Generating fallback response | provider=%s", provider)
    system_prompt = build_system_prompt(anonymized_profile)
    response = _call_llm_provider(
        provider, model, temperature, system_prompt, history, sanitized_message,
        attachments=attachments
    )

    if response is None:
        logger.error("[General LLM] Unsupported provider '%s'; returning error message.", provider)
        return "I'm sorry, the configured AI provider is not available. Please check your settings."

    return response


def _run_deanonymise(ai_response, conversation_id):
    """
    Step 4 — Guardian Agent: Re-hydrates PII tokens back into the response.
    Returns the final clean response.
    """
    logger.debug("[Guardian] Starting de-anonymisation | conv=%s", conversation_id)
    final_response = sanitizer.deanonymize_response(ai_response)
    historian.log_step(
        session_id=conversation_id,
        agent_name="Guardian",
        step_type="RESPONSE",
        content="Response de-anonymized and ready for customer delivery.",
    )
    logger.info("[Guardian] De-anonymisation complete | conv=%s", conversation_id)
    return final_response


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def generate_ai_response(
    message, user_profile=None, conversation_history=None, llm_config=None, 
    conversation_id=None, attachments=None
):
    """
    Full agentic pipeline for a single user message.
    Orchestrates the Guardian, Dispatcher, and Specialist Agents in a single flow.
    """
    logger.info("generate_ai_response started | conv=%s multimodal=%s", 
                conversation_id, bool(attachments))

    # Phase 1: Preparation & PII Anonymisation
    config = _resolve_llm_config()
    sanitized_message, anonymized_profile = _run_pii_scrub(message, user_profile, conversation_id)

    # Phase 2: Intent-based Routing (Specialist Agents)
    # The Dispatcher internally handles Empath sentiment analysis and Guardrails
    agent_response = _run_dispatch(sanitized_message, user_profile, conversation_history, conversation_id)
    if agent_response:
        return agent_response

    # Phase 3: General Intelligence Fallback (Multimodal-ready)
    ai_response = _run_general_llm(
        config["provider"], config["modelName"], config["temperature"],
        anonymized_profile, conversation_history, sanitized_message, 
        attachments=attachments
    )

    # Phase 4: PII De-anonymisation
    final_response = _run_deanonymise(ai_response, conversation_id)

    logger.info("generate_ai_response complete | conv=%s", conversation_id)
    return final_response


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def validate_intent_response(api_response):
    """Returns True if the api_response is a valid JSON object."""
    if isinstance(api_response, dict):
        return True
    if isinstance(api_response, str):
        try:
            json.loads(api_response.replace("'", '"'))
            return True
        except json.JSONDecodeError:
            return False
    return False


def extract_json(input_text):
    """Extracts the first JSON object found in a freeform string."""
    match = re.search(r"\{.*\}", input_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("extract_json: regex matched but JSON decode failed.")
            return input_text
    return input_text


def generate_suggested_questions(message, response):
    """Returns a static set of contextual follow-up questions."""
    import uuid
    return [
        {"id": str(uuid.uuid4()), "text": "How much do I need to save monthly?", "category": "planning"},
        {"id": str(uuid.uuid4()), "text": "What investment strategy is best for me?", "category": "investment"},
        {"id": str(uuid.uuid4()), "text": "How does inflation affect my retirement?", "category": "planning"},
        {"id": str(uuid.uuid4()), "text": "What are tax advantages of retirement accounts?", "category": "investment"},
    ]
