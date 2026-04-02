import jwt
from datetime import datetime, timedelta, timezone
from app.utils.auth import token_required
from app.utils.pii_sanitizer import PIISanitizer
from flask import jsonify

def test_token_required_missing(app, client):
    @app.route('/dummy')
    @token_required
    def dummy(current_user):
        return jsonify({"success": True})
        
    res = client.get('/dummy')
    assert res.status_code == 401
    assert "missing" in res.get_json()["message"]

def test_token_required_valid(app, client, seed_data):
    @app.route('/dummy-valid')
    @token_required
    def dummy_valid(current_user):
        return jsonify({"user": current_user.username})
        
    token = jwt.encode(
        {"user_id": seed_data["user_id"]},
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    res = client.get('/dummy-valid', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["user"] == "testuser"

def test_token_required_expired(app, client, seed_data):
    @app.route('/dummy-expired')
    @token_required
    def dummy_expired(current_user):
        return jsonify({"success": True})
        
    token = jwt.encode(
        {"user_id": seed_data["user_id"], "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    res = client.get('/dummy-expired', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert "expired" in res.get_json()["message"]
    
def test_token_required_invalid(app, client):
    @app.route('/dummy-invalid')
    @token_required
    def dummy_invalid(current_user):
        return jsonify({"success": True})
        
    res = client.get('/dummy-invalid', headers={"Authorization": "Bearer badtoken"})
    assert res.status_code == 401
    
def test_token_user_not_found(app, client):
    @app.route('/dummy-notfound')
    @token_required
    def dummy_missing(current_user):
        return jsonify({"success": True})
        
    token = jwt.encode(
        {"user_id": "nonexistent"},
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    res = client.get('/dummy-notfound', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert "not found" in res.get_json()["message"].lower()

def test_pii_sanitizer():
    sanitizer = PIISanitizer()
    profile = {
        "name": "Sarah Connor",
        "email": "sarah@connor.com"
    }
    sanitized_str = sanitizer.sanitize_profile_to_string(profile)
    assert "Sarah Connor" not in sanitized_str
    assert "sarah@connor.com" not in sanitized_str
    
    # We should have at least one mapping item
    assert len(sanitizer.mapping) > 0
    
    # If the tokenizer successfully hid it, lets see if our rehydration works
    llm_resp = "Hello " + list(sanitizer.mapping.keys())[0] + ", how are you?"
    rehydrated = sanitizer.deanonymize_response(llm_resp)
    
    # Verify that the replaced text is no longer exactly the key, but its original text
    assert "Sarah Connor" in rehydrated or "sarah@connor.com" in rehydrated
