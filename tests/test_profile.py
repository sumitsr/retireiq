import json
import jwt
import pytest
from app.models.user import User
from app import db

@pytest.fixture
def auth_token(app, seed_data):
    return jwt.encode({"user_id": seed_data["user_id"]}, app.config["SECRET_KEY"], algorithm="HS256")

def test_get_profile_success(client, auth_token, seed_data):
    res = client.get('/api/profile/', headers={"Authorization": f"Bearer {auth_token}"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["user_id"] == seed_data["user_id"]
    assert data["email"] == "test@user.com"

def test_get_profile_unauth_route_success(client, seed_data):
    res = client.get(f'/api/profile/unauth?user_id={seed_data["user_id"]}')
    assert res.status_code == 200
    data = res.get_json()
    assert data["personal_details"]["contact_details"]["email"] == "test@user.com"

def test_get_profile_unauth_route_missing_id(client):
    res = client.get('/api/profile/unauth')
    assert res.status_code == 400
    assert "Missing user_id" in res.get_json()["message"]

def test_get_profile_unauth_route_not_found(client):
    res = client.get('/api/profile/unauth?user_id=nonexistent')
    assert res.status_code == 404
    assert "User not found" in res.get_json()["message"]

def test_update_profile_all_fields(client, auth_token, seed_data, app):
    update_data = {
        "personal_details": {"age": 45, "occupation": "Software Engineer"},
        "financial_profile": {"totalAssets": 500000, "annualIncome": 150000},
        "risk_profile": {"riskTolerance": "Moderate"},
        "financial_goals": {"retirementAge": 60},
        "product_eligibility": {"qualifiedInvestor": True},
        "regulatory_compliance": {"politicallyExposed": False},
        "cognitive_digital_accessibility": {"fontSize": "large"},
        "product_offerings": {"preferredBanks": ["Bank A"]},
        "tax_efficiency": {"taxBracket": "32%"}
    }
    
    res = client.put('/api/profile/', 
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    assert res.status_code == 200
    
    # Verify in DB
    with app.app_context():
        user = db.session.get(User, seed_data["user_id"])
        assert user.personal_details["age"] == 45
        assert user.financial_profile["totalAssets"] == 500000
        assert user.risk_profile["riskTolerance"] == "Moderate"
        assert user.financial_goals["retirementAge"] == 60
        assert user.product_eligibility["qualifiedInvestor"] is True
        assert user.regulatory_compliance["politicallyExposed"] is False
        assert user.cognitive_digital_accessibility["fontSize"] == "large"
        assert user.product_offerings["preferredBanks"] == ["Bank A"]
        assert user.tax_efficiency["taxBracket"] == "32%"

def test_update_profile_no_data(client, auth_token):
    res = client.put('/api/profile/', 
        headers={"Authorization": f"Bearer {auth_token}"},
        json={} 
    )
    assert res.status_code == 400
    assert "No data provided" in res.get_json()["message"]
