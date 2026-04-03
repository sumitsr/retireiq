import json
import pytest
from unittest.mock import patch, MagicMock
from app.services.memory_service import summarize_into_facts
from app.models.chat import Conversation, Message
from app.models.user_memory import UserMemory
from app import db

@patch("app.services.memory_service.create_app")
@patch("app.services.memory_service.call_azure_openai_api_with_key")
@patch("app.services.memory_service.call_openai_api")
def test_summarize_into_facts_success(mock_openai, mock_azure, mock_create_app, app, seed_data):
    # Setup mocks
    mock_create_app.return_value = app
    mock_azure.return_value = json.dumps(["User prefers ESG funds", "Goal: retire at 60"])
    
    with app.app_context():
        user_id = seed_data["user_id"]
        # Create a conversation with messages
        convo = Conversation(user_id=user_id)
        db.session.add(convo)
        db.session.flush() # Get convo.id
        
        msg1 = Message(conversation_id=convo.id, type="user", content="I want ESG funds only.")
        msg2 = Message(conversation_id=convo.id, type="bot", content="Understood.")
        db.session.add_all([msg1, msg2])
        db.session.commit()
        
        # Run service
        summarize_into_facts(user_id, convo.id)
        
        # Verify
        memories = UserMemory.query.filter_by(user_id=user_id).all()
        assert len(memories) == 2
        texts = [m.fact_text for m in memories]
        assert "User prefers ESG funds" in texts
        assert "Goal: retire at 60" in texts

@patch("app.services.memory_service.create_app")
def test_summarize_into_facts_no_convo(mock_create_app, app):
    mock_create_app.return_value = app
    with app.app_context():
        # Should return early gracefully if conversation not found
        summarize_into_facts("u1", "non_existent_convo")

@patch("app.services.memory_service.create_app")
def test_summarize_into_facts_no_messages(mock_create_app, app, seed_data):
    mock_create_app.return_value = app
    with app.app_context():
        user_id = seed_data["user_id"]
        convo = Conversation(user_id=user_id)
        db.session.add(convo)
        db.session.commit()
        
        # No messages in convo
        summarize_into_facts(user_id, convo.id)
        
        memories = UserMemory.query.filter_by(user_id=user_id).all()
        assert len(memories) == 0

@patch("app.services.memory_service.create_app")
@patch("app.services.memory_service.call_azure_openai_api_with_key")
def test_summarize_into_facts_invalid_json(mock_azure, mock_create_app, app, seed_data):
    mock_create_app.return_value = app
    mock_azure.return_value = "not a json"
    
    with app.app_context():
        user_id = seed_data["user_id"]
        convo = Conversation(user_id=user_id)
        db.session.add(convo)
        db.session.flush()
        msg1 = Message(conversation_id=convo.id, type="user", content="I want ESG funds only.")
        db.session.add(msg1)
        db.session.commit()
        
        # Should handle JSON decode error gracefully
        summarize_into_facts(user_id, convo.id)
        
        memories = UserMemory.query.filter_by(user_id=user_id).all()
        assert len(memories) == 0

@patch("app.services.memory_service.create_app")
@patch("app.services.memory_service.call_openai_api")
def test_summarize_into_facts_openai_provider(mock_openai, mock_create_app, app, seed_data, monkeypatch):
    mock_create_app.return_value = app
    mock_openai.return_value = json.dumps(["Fact 1"])
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    
    with app.app_context():
        user_id = seed_data["user_id"]
        convo = Conversation(user_id=user_id)
        db.session.add(convo)
        db.session.flush()
        msg1 = Message(conversation_id=convo.id, type="user", content="Hello.")
        db.session.add(msg1)
        db.session.commit()
        
        summarize_into_facts(user_id, convo.id)
        
        assert mock_openai.called
        memories = UserMemory.query.filter_by(user_id=user_id).all()
        assert len(memories) == 1
