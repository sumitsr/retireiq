import os
import json
import pytest
from unittest.mock import patch, MagicMock
from app.services.llm_service import (
    build_system_prompt,
    prepare_openai_messages,
    call_ollama_api,
    generate_ai_response,
    extract_json,
    validate_intent_response
)

def test_build_system_prompt():
    profile = json.dumps({"memories": ["Fact 1", "Fact 2"], "personal_details": {"first_name": "Test"}})
    prompt = build_system_prompt(profile)
    assert "RetireIQ" in prompt
    assert "Fact 1" in prompt
    assert "Test" in prompt

def test_prepare_openai_messages():
    system_prompt = "System Rule"
    history = [
        {"type": "user", "content": "hello"},
        {"type": "bot", "content": "hi"}
    ]
    message = "how are you?"
    messages = prepare_openai_messages(system_prompt, history, message)
    
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "hello"
    assert messages[2]["role"] == "assistant"
    assert messages[3]["content"] == "how are you?"

@patch("requests.post")
def test_call_ollama_api_success(mock_post):
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": {"content": "Ollama response"}}
    mock_post.return_value = mock_response
    
    res = call_ollama_api([{"role": "user", "content": "hi"}], "llama3", 0.7)
    assert res == "Ollama response"

@patch("requests.post")
def test_call_ollama_api_failure(mock_post):
    # Mock failure
    mock_post.side_effect = Exception("Connection error")
    
    res = call_ollama_api([], "llama3", 0.7)
    assert "encountered an error with the local Ollama service" in res

def test_extract_json():
    text = "Some text before {\"key\": \"value\"} some text after"
    result = extract_json(text)
    assert result == {"key": "value"}
    
    text_no_json = "just plain text"
    assert extract_json(text_no_json) == "just plain text"

def test_validate_intent_response():
    assert validate_intent_response({"intent": "test"}) is True
    assert validate_intent_response("{\"intent\": \"test\"}") is True
    assert validate_intent_response("invalid json") is False

@patch("app.services.llm_service.dispatcher.dispatch")
def test_generate_ai_response_ollama_intent(mock_dispatch):
    # In the new architecture, the dispatcher handles intent routing.
    mock_dispatch.return_value = "Agent Result"

    os.environ["LLM_PROVIDER"] = "ollama"

    res = generate_ai_response("I want to invest in stocks", user_profile={"id": "u1"})

    assert res == "Agent Result"
    mock_dispatch.assert_called_once()

@patch("openai.OpenAI")
def test_call_openai_api_success(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance
    mock_instance.chat.completions.create.return_value.choices[0].message.content = "OpenAI response"
    
    from app.services.llm_service import call_openai_api
    res = call_openai_api([], "gpt-4", 0.7)
    assert res == "OpenAI response"

@patch("openai.ChatCompletion.create")
def test_call_azure_openai_api_success(mock_create):
    mock_create.return_value = {"choices": [{"message": {"content": "Azure response"}}]}
    
    os.environ["AZURE_OPENAI_API_KEY"] = "test"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "test"
    
    from app.services.llm_service import call_azure_openai_api_with_key
    res = call_azure_openai_api_with_key([], "gpt-4", 0.7)
    assert res == "Azure response"

def test_generate_ai_response_invalid_provider():
    os.environ["LLM_PROVIDER"] = "invalid"
    with patch("app.services.llm_service.dispatcher.dispatch", return_value=None):
        res = generate_ai_response("hi")
    assert "configured AI provider is not available" in res

def test_prepare_azure_openai_messages():
    from app.services.llm_service import prepare_azure_openai_messages
    res = prepare_azure_openai_messages("prompt", [], "msg")
    assert len(res) == 2
    assert res[0]["role"] == "system"

def test_generate_suggested_questions():
    from app.services.llm_service import generate_suggested_questions
    res = generate_suggested_questions("hi", "bye")
    assert len(res) == 4
    for q in res:
        assert "text" in q
        assert "id" in q

@patch("app.services.llm_service.call_azure_openai_api_with_key")
def test_generate_ai_response_azure_success(mock_azure_call):
    mock_azure_call.return_value = "Azure Hello"
    os.environ["LLM_PROVIDER"] = "azure_openai"
    with patch("app.services.llm_service.dispatcher.dispatch", return_value=None):
        res = generate_ai_response("hi", user_profile={"id": "u1"})
    assert res == "Azure Hello"

@patch("openai.OpenAI")
def test_call_openai_api_no_key(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance
    mock_instance.api_key = None
    
    from app.services.llm_service import call_openai_api
    res = call_openai_api([], "gpt-4", 0.7)
    assert "not configured correctly" in res

@patch("openai.OpenAI")
def test_call_openai_api_exception(mock_openai):
    mock_openai.side_effect = Exception("OpenAI Error")
    from app.services.llm_service import call_openai_api
    res = call_openai_api([], "gpt-4", 0.7)
    assert "encountered an error" in res

def test_call_azure_openai_api_no_config():
    if "AZURE_OPENAI_API_KEY" in os.environ:
        del os.environ["AZURE_OPENAI_API_KEY"]
    from app.services.llm_service import call_azure_openai_api_with_key
    res = call_azure_openai_api_with_key([], "gpt-4")
    assert "not configured correctly" in res

@patch("openai.ChatCompletion.create")
def test_call_azure_openai_api_exception(mock_create):
    mock_create.side_effect = Exception("Azure Error")
    os.environ["AZURE_OPENAI_API_KEY"] = "test"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "test"
    from app.services.llm_service import call_azure_openai_api_with_key
    res = call_azure_openai_api_with_key([], "gpt-4")
    assert "encountered an error" in res
