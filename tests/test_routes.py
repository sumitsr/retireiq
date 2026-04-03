import json
import jwt
import pytest
from unittest.mock import patch, MagicMock

def test_auth_register(client):
    res = client.post('/api/auth/register', json={
        "email": "new@user.com",
        "password": "password123",
        "firstName": "New",
        "lastName": "User"
    })
    assert res.status_code == 201
    assert "token" in res.get_json()

def test_auth_login(client, seed_data):
    with patch("app.models.user.check_password_hash", return_value=True):
        res = client.post('/api/auth/login', json={
            "email": "test@user.com",
            "password": "any"
        })
        assert res.status_code == 200
        assert "token" in res.get_json()

def test_get_profile(client, app, seed_data):
    token = jwt.encode({"user_id": seed_data["user_id"]}, app.config["SECRET_KEY"], algorithm="HS256")
    res = client.get('/api/profile/', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["email"] == "test@user.com"

def test_update_profile(client, app, seed_data):
    token = jwt.encode({"user_id": seed_data["user_id"]}, app.config["SECRET_KEY"], algorithm="HS256")
    res = client.put('/api/profile/', 
        headers={"Authorization": f"Bearer {token}"},
        json={"financial_profile": {"totalAssets": 250000}}
    )
    assert res.status_code == 200
    assert "Profile updated successfully" in res.get_json()["message"]

@patch("app.services.llm_service.generate_ai_response", return_value="Mocked AI Response")
def test_chat(mock_gen, client, app, seed_data):
    token = jwt.encode({"user_id": seed_data["user_id"]}, app.config["SECRET_KEY"], algorithm="HS256")
    
    res = client.post('/api/chat/message', 
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hello", "stream": False}
    )
    assert res.status_code == 200
    assert "Mocked AI Response" in res.get_json()["message"]["content"]

@patch("app.routes.recommend.recommend_products")
def test_recommend(mock_rec, client, app, seed_data):
    mock_rec.return_value = {"recommendations": [{"id": "p1", "name": "Prod 1"}]}
    token = jwt.encode({"user_id": seed_data["user_id"]}, app.config["SECRET_KEY"], algorithm="HS256")
    
    res = client.get('/api/recommend/', 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert len(res.get_json()["recommendations"]) == 1
