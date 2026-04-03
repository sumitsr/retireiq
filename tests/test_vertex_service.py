import pytest
import os
from unittest.mock import patch, MagicMock
from app.services.llm_service import call_vertex_ai_api, generate_ai_response
from app.services.knowledge_service import cache_manager

def test_vertex_ai_api_call_mock():
    """Verify that vertex ai api call correctly uses the SDK."""
    # We need to patch both vertexai AND the individual classes since they default to None
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = "GCP Response"
    mock_model_class = MagicMock(return_value=mock_model)
    mock_gen_config = MagicMock()

    with patch.multiple(
        'app.services.llm_service',
        vertexai=MagicMock(),
        GenerativeModel=mock_model_class,
        GenerationConfig=MagicMock(return_value=mock_gen_config),
    ):
        response = call_vertex_ai_api("Hello", model_name="gemini-1.5-pro")

        assert response == "GCP Response"
        mock_model_class.assert_called_with("gemini-1.5-pro")

def test_model_tiering_logic(app):
    """Verify that vertex_ai provider triggers the correct model tiering."""
    with app.app_context():
        # Setup environment, clearing LLM_MODEL_NAME to test the automated default
        with patch.dict(os.environ, {"LLM_PROVIDER": "vertex_ai", "GCP_PROJECT_ID": "test-project", "LLM_MODEL_NAME": ""}):
             with patch('app.services.llm_service.call_vertex_ai_api', return_value="Model Tiering Success") as mock_vertex_call:
                 # Mock dispatcher to return None so we hit the general LLM fallback
                 with patch('app.services.llm_service.dispatcher.dispatch', return_value=None):
                     
                     generate_ai_response("General chat")
                     
                     # Check that the default Pro model was called for general chat
                     args, _ = mock_vertex_call.call_args
                     assert args[1] == "gemini-1.5-pro"

def test_vertex_context_cache_creation():
    """Verify that VertexCacheManager correctly attempts to create a cache."""
    with patch('app.services.knowledge_service.vertexai') as mock_v:
        # Mocking the caching object itself
        mock_caching = MagicMock()
        with patch('app.services.knowledge_service.caching', mock_caching):
            mock_caching.CachedContent.create.return_value.name = "cached_policy_123"
            
            cache_id = cache_manager.create_policy_cache("Large Policy Content...")
            
            assert cache_id == "cached_policy_123"
            mock_caching.CachedContent.create.assert_called_once()
            _, kwargs = mock_caching.CachedContent.create.call_args
            assert "gemini" in kwargs['model_name']
