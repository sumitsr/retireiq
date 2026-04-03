import pytest
from unittest.mock import patch, MagicMock
from app.services.knowledge_service import knowledge_service
from app.models.knowledge import KnowledgeChunk

@patch("requests.post")
def test_get_embedding_success(mock_post):
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mock_post.return_value = mock_response
    
    res = knowledge_service.get_embedding("test text")
    assert res == [0.1, 0.2, 0.3]

@patch("requests.post")
def test_get_embedding_failure(mock_post):
    # Mock failure
    mock_post.side_effect = Exception("Connection error")
    
    res = knowledge_service.get_embedding("test text")
    assert res is None

@patch("app.services.knowledge_service.KnowledgeService.get_embedding")
@patch("app.db.session.add")
@patch("app.db.session.commit")
@patch("app.models.knowledge.KnowledgeChunk.query")
def test_add_knowledge_chunk_success(mock_query, mock_commit, mock_add, mock_get_embedding, app):
    mock_get_embedding.return_value = [0.1, 0.2, 0.3]
    
    # Mocking query.filter_by().first()
    mock_filter = MagicMock()
    mock_filter.first.return_value = KnowledgeChunk(content="Test content", meta_data={"source": "test"})
    mock_query.filter_by.return_value = mock_filter
    
    with app.app_context():
        success = knowledge_service.add_knowledge_chunk("Test content", {"source": "test"})
        assert success is True
        mock_add.assert_called_once()
        mock_commit.assert_called_once()

@patch("app.services.knowledge_service.KnowledgeService.get_embedding")
def test_add_knowledge_chunk_failure(mock_get_embedding, app):
    mock_get_embedding.return_value = None
    
    with app.app_context():
        success = knowledge_service.add_knowledge_chunk("Test content failure")
        assert success is False

@patch("app.services.knowledge_service.KnowledgeService.get_embedding")
@patch("app.models.knowledge.KnowledgeChunk.query")
def test_query_knowledge_success(mock_query, mock_get_embedding, app):
    mock_get_embedding.return_value = [0.1, 0.2, 0.3]
    
    # Mocking the complex query chain KnowledgeChunk.query.order_by(...).limit(...).all()
    mock_all = MagicMock()
    mock_all.all.return_value = [KnowledgeChunk(content="Target finding", id=1)]
    mock_limit = MagicMock()
    mock_limit.limit.return_value = mock_all
    mock_query.order_by.return_value = mock_limit
    
    with app.app_context():
        results = knowledge_service.query_knowledge("find me something")
        assert len(results) >= 1
        assert results[0].content == "Target finding"
        mock_query.order_by.assert_called_once()
