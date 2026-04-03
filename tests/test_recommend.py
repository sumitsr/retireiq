import pytest
import jwt
from unittest.mock import patch, MagicMock
from app.models.product import Product

@pytest.fixture
def auth_token(app, seed_data):
    return jwt.encode({"user_id": seed_data["user_id"]}, app.config["SECRET_KEY"], algorithm="HS256")

@patch("app.routes.recommend.recommend_products")
def test_recommend_success(mock_recommend, client, auth_token, seed_data):
    mock_recommend.return_value = {"recommendations": [{"id": "test_prod_1", "name": "Test Fund"}]}
    
    res = client.get('/api/recommend/', headers={"Authorization": f"Bearer {auth_token}"})
    assert res.status_code == 200
    assert len(res.get_json()["recommendations"]) == 1

@patch("app.routes.recommend.recommend_products")
def test_recommend_unauth_route_success(mock_recommend, client, seed_data):
    mock_recommend.return_value = {"recommendations": []}
    res = client.get(f'/api/recommend/unauth?user_id={seed_data["user_id"]}')
    assert res.status_code == 200
    assert "recommendations" in res.get_json()

def test_recommend_unauth_route_missing_id(client):
    res = client.get('/api/recommend/unauth')
    assert res.status_code == 400
    assert "Missing user_id" in res.get_json()["message"]

def test_recommend_unauth_route_not_found(client):
    res = client.get('/api/recommend/unauth?user_id=nonexistent')
    assert res.status_code == 404
    assert "User not found" in res.get_json()["message"]
