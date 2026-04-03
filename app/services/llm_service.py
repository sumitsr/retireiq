import os
import json
import re
import requests
from app.services.agent_service import call_agent_api

try:
    import openai
except ImportError:
    pass

try:
    import anthropic
except ImportError:
    pass

from app.utils.pii_sanitizer import sanitizer


def build_system_prompt(user_profile_string=""):
    import json

    try:
        parsed = json.loads(user_profile_string)
        memories = parsed.get("memories", [])
    except:
        memories = []

    system_prompt = f"""
    As RetireIQ, a retirement agent chatbot with access to the customer's structured personal and financial data in JSON format, begin a short, personalized conversation to guide the customer toward the sub-intent "Choose retirement investments." First, extract the customer's first name from the field personal_details.first_name and use it naturally to address them throughout the interaction. Acknowledge their current financial stage without repeating known details. Ask if they’re currently more focused on growing long-term retirement savings or keeping flexibility for short-term needs. Based on their response, follow up to understand whether they prefer a hands-on investment style or an automated, guided approach. If needed, ask if they have specific preferences or exclusions (e.g., ESG, sectors to avoid). Keep the conversation friendly and concise, ask only relevant questions (up to five), and stop once enough information is gathered to recommend suitable retirement investment options tailored to their goals and preferences.

    Once intent and sub-intent are known, output your understanding in the following structured JSON format only and don't add any other text anywhere in response:
    {{
        "intent": "<detected primary intent>",
        "sub_intent": "<detected sub-intent details>",
        "summary": "<short natural-language summary of what the customer wants>"
    }}

    Historical Context / Permanent Memories:
    {json.dumps(memories)}

    User Profile Data: {user_profile_string}
    """
    return system_prompt


def prepare_openai_messages(system_prompt, conversation_history, message):
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        for msg in conversation_history:
            if msg["type"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["type"] == "bot":
                messages.append({"role": "assistant", "content": msg["content"]})
    messages.append({"role": "user", "content": message})
    return messages


def prepare_azure_openai_messages(system_prompt, conversation_history, message):
    return prepare_openai_messages(system_prompt, conversation_history, message)


def call_openai_api(messages, model, temperature):
    try:
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        if not client.api_key:
            return "I'm sorry, the OpenAI API key is not configured correctly."
        response = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature, max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return f"I'm sorry, I encountered an error processing your request: {e}"


def call_ollama_api(messages, model, temperature):
    try:
        base_url = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
        url = f"{base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        return response.json().get("message", {}).get("content", "")
    except Exception as e:
        print(f"Error with Ollama API: {e}")
        return f"I'm sorry, I encountered an error with the local Ollama service: {e}"


def call_azure_openai_api_with_key(messages, model, temperature=0.7, max_tokens=500):
    try:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")

        if not api_key or not api_base:
            return "I'm sorry, the Azure OpenAI API key or endpoint is not configured correctly."

        openai.api_type = "azure"
        openai.api_key = api_key
        openai.api_base = api_base
        openai.api_version = api_version

        response = openai.ChatCompletion.create(
            engine=model, messages=messages, temperature=temperature, max_tokens=max_tokens
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error with Azure OpenAI API: {e}")
        return f"I'm sorry, I encountered an error processing your request: {e}"


def generate_ai_response(message, user_profile=None, conversation_history=None, llm_config=None):
    llm_config = {
        "provider": os.getenv("LLM_PROVIDER", "azure_openai"),
        "modelName": os.getenv("LLM_MODEL_NAME", "gpt-4o"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", 0.7)),
    }
    provider = llm_config.get("provider")
    model = llm_config.get("modelName")
    temperature = llm_config.get("temperature")

    # 0. Session Isolation: Clear previous mappings
    sanitizer.clear_mapping()

    # 1. PII Scrubbing of the user profile dictionary
    anonymized_profile = sanitizer.sanitize_profile_to_string(user_profile if user_profile else {})

    # 2. PII Scrubbing of the incoming user message
    sanitized_message, message_mapping = sanitizer.sanitize_text(message)
    # Merge message mapping into global mapping for re-hydration
    sanitizer.mapping.update(message_mapping)

    system_prompt = build_system_prompt(anonymized_profile)

    ai_response = ""

    if provider == "openai":
        messages = prepare_openai_messages(system_prompt, conversation_history, sanitized_message)
        ai_response = call_openai_api(messages, model, temperature)
    elif provider == "azure_openai":
        prompt = prepare_azure_openai_messages(system_prompt, conversation_history, sanitized_message)
        ai_response = call_azure_openai_api_with_key(prompt, model, temperature)
    elif provider == "ollama":
        messages = prepare_openai_messages(system_prompt, conversation_history, sanitized_message)
        ai_response = call_ollama_api(messages, model, temperature)
    else:
        return "I'm sorry, the configured AI provider is not available. Please check your settings."

    # 2. De-anonymize back to original names.
    deanonymized_ai_response = sanitizer.deanonymize_response(ai_response)

    print(f"AI Response: {deanonymized_ai_response}")
    extrectedAIResponse = extract_json(deanonymized_ai_response)

    if validate_intent_response(extrectedAIResponse):
        print(f"Intent and sub-intent identified, calling agent: {extrectedAIResponse}")
        user_id = user_profile.get("id", "") if isinstance(user_profile, dict) else ""
        final_res = call_agent_api(extrectedAIResponse, user_id)
        return final_res
    else:
        return deanonymized_ai_response


def validate_intent_response(api_response):
    if isinstance(api_response, dict):
        return True
    elif isinstance(api_response, str):
        try:
            corrected_str = api_response.replace("'", '"')
            json.loads(corrected_str)
            return True
        except json.JSONDecodeError:
            return False
    return False


def extract_json(input_text):
    match = re.search(r"\{.*\}", input_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return input_text
    return input_text


def generate_suggested_questions(message, response):
    import uuid

    return [
        {
            "id": str(uuid.uuid4()),
            "text": "How much do I need to save monthly?",
            "category": "planning",
        },
        {
            "id": str(uuid.uuid4()),
            "text": "What investment strategy is best for me?",
            "category": "investment",
        },
        {
            "id": str(uuid.uuid4()),
            "text": "How does inflation affect my retirement?",
            "category": "planning",
        },
        {
            "id": str(uuid.uuid4()),
            "text": "What are tax advantages of retirement accounts?",
            "category": "investment",
        },
    ]
