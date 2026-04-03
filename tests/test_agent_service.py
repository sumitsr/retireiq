import pytest
from unittest.mock import patch, MagicMock
from app.services.agent_service import call_agent_api, call_agent_api_get_final_response, generateAgentAPIToken

def test_generate_agent_api_token_no_cookies():
    # This function just prints, so we just verify it doesn't crash
    with patch("browser_cookie3.load", side_effect=Exception("No cookies")):
        generateAgentAPIToken()

@patch("requests.post")
@patch("app.services.agent_service.call_agent_api_get_final_response")
def test_call_agent_api_success(mock_get_final, mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"correlation_id": "123"}
    mock_get_final.return_value = "Agent Final Answer"
    
    res = call_agent_api({"intent": "invest"}, "user1")
    assert res == "Agent Final Answer"
    mock_get_final.assert_called_once_with("123")

@patch("requests.post")
def test_call_agent_api_failure(mock_post):
    mock_post.return_value.status_code = 500
    res = call_agent_api("invest", "user1")
    assert "Something went wrong" in res

@patch("requests.get")
def test_call_agent_api_get_final_response_completed(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        {
            "agentStatus": "completed",
            "output": {"response_text": "Task finished"}
        }
    ]
    
    res = call_agent_api_get_final_response("123")
    assert res == "Task finished"

@patch("requests.get")
@patch("time.sleep", return_value=None)
def test_call_agent_api_get_final_response_pending_then_complete(mock_sleep, mock_get):
    # First call returns pending, second returns completed
    resp_pending = MagicMock()
    resp_pending.status_code = 200
    resp_pending.json.return_value = [{"agentStatus": "pending"}]
    
    resp_complete = MagicMock()
    resp_complete.status_code = 200
    resp_complete.json.return_value = [{"agentStatus": "completed", "output": {"response_text": "Done"}}]
    
    mock_get.side_effect = [resp_pending, resp_complete]
    
    res = call_agent_api_get_final_response("123")
    assert res == "Done"
    assert mock_sleep.call_count == 1
