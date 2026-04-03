import pytest
import json
from unittest.mock import patch
from app.services.guardrails_service import GuardrailsService

@pytest.fixture
def guardrails():
    # Force provider to azure_openai for predictable test patching
    import os
    os.environ["LLM_PROVIDER"] = "azure_openai"
    return GuardrailsService()

def test_safe_query_passes(guardrails):
    # Mock LLM API returning a PASS status
    mock_response = json.dumps({
        "status": "PASS",
        "reason": "OK",
        "refusal_message": ""
    })
    
    with patch("app.services.llm_service.call_azure_openai_api_with_key", return_value=mock_response):
        refusal = guardrails.check_query_sync("What is a 401k?")
        assert refusal is None

def test_medical_query_blocked(guardrails):
    # Mock LLM API returning a BLOCK for medical
    msg = "I am a Financial Advisor, not a medical professional."
    mock_response = json.dumps({
        "status": "BLOCK",
        "reason": "MEDICAL",
        "refusal_message": msg
    })
    
    with patch("app.services.llm_service.call_azure_openai_api_with_key", return_value=mock_response):
        refusal = guardrails.check_query_sync("I have a pain in my chest.")
        assert refusal == msg

def test_off_topic_query_blocked(guardrails):
    msg = "I am specifically trained as a Retirement Advisor."
    mock_response = json.dumps({
        "status": "BLOCK",
        "reason": "OFF_TOPIC",
        "refusal_message": msg
    })
    
    with patch("app.services.llm_service.call_azure_openai_api_with_key", return_value=mock_response):
        refusal = guardrails.check_query_sync("Who won the game?")
        assert refusal == msg

def test_json_parse_fallthrough(guardrails):
    # Mock an invalid JSON response
    with patch("app.services.llm_service.call_azure_openai_api_with_key", return_value="Not JSON"):
        refusal = guardrails.check_query_sync("Any query")
        # Should fallback to PASS
        assert refusal is None
