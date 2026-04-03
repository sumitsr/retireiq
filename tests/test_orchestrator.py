import pytest
from unittest.mock import patch, MagicMock
from app.services.orchestrator import dispatcher
from app.models.audit import AgentAudit
from app import db

def test_orchestrator_classification_knowledge(app):
    """Test that policy questions are routed to the Knowledge Base."""
    with app.app_context():
        # Mock the LLM classification response
        mock_intent = {"intent": "KNOWLEDGE_BASE", "sub_intent": "policy query", "confidence": 0.95}
        
        with patch.object(dispatcher, '_classify_intent', return_value=mock_intent):
            with patch.object(dispatcher, '_handle_knowledge_query', return_value="Knowledge Results") as mock_handle:
                response = dispatcher.dispatch("What is a 401k?", {}, [], "test-session-123")
                
                assert response == "Knowledge Results"
                mock_handle.assert_called_once()
                
                # Verify Audit Trail
                audits = AgentAudit.query.filter_by(session_id="test-session-123").all()
                assert len(audits) >= 2
                assert audits[0].agent_name == "Dispatcher"
                assert audits[1].step_type == "ACTION"
                assert "Intent resolved: KNOWLEDGE_BASE" in audits[1].content

def test_orchestrator_classification_transaction(app):
    """Test that trade requests are routed to the Transaction agent."""
    with app.app_context():
        mock_intent = {"intent": "TRANSACTIONAL", "sub_intent": "buy stock", "confidence": 0.99}
        
        with patch.object(dispatcher, '_classify_intent', return_value=mock_intent):
            with patch('app.services.orchestrator.call_agent_api', return_value="Trade Executed") as mock_agent_call:
                response = dispatcher.dispatch("Buy 10 shares of AAPL", {"id": "user-1"}, [], "test-session-456")
                
                assert response == "Trade Executed"
                mock_agent_call.assert_called_once()

def test_orchestrator_fallback_to_general(app):
    """Test that general chit-chat returns None (falling back to general LLM)."""
    with app.app_context():
        mock_intent = {"intent": "GENERAL", "sub_intent": "greeting", "confidence": 0.8}
        
        with patch.object(dispatcher, '_classify_intent', return_value=mock_intent):
            response = dispatcher.dispatch("Hello there!", {}, [], "test-session-789")
            
            assert response is None
            
            # Verify Audit Trail even for General intent
            audit = AgentAudit.query.filter_by(session_id="test-session-789", step_type="ACTION").first()
            assert audit.content == "Intent resolved: GENERAL"
