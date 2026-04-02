from app.models.user import User
from app.models.chat import Conversation, Message
from app.models.product import Product
from app import db

def test_user_password_hashing(app):
    with app.app_context():
        u = User(id="u1", email="test@test.com")
        u.set_password("mypassword")
        assert u.check_password("mypassword") is True
        assert u.check_password("wrong") is False

def test_user_creation(app, seed_data):
    with app.app_context():
        u = db.session.get(User, seed_data["user_id"])
        udict = u.to_dict()
        assert udict["personal_details"]["first_name"] == "Test"
        assert udict["financial_profile"]["totalAssets"] == 100000.0

def test_chat_memory(app, seed_data):
    with app.app_context():
        convo = Conversation(user_id=seed_data["user_id"])
        db.session.add(convo)
        db.session.commit()
        
        msg = Message(conversation_id=convo.id, content="hello", type="user")
        db.session.add(msg)
        db.session.commit()
        
        saved_msg = Message.query.filter_by(conversation_id=convo.id).first()
        assert saved_msg.content == "hello"
        assert saved_msg.to_dict()["type"] == "user"

def test_product(app, seed_data):
    with app.app_context():
        p = db.session.get(Product, seed_data["product_id"])
        assert p.name == "Test Aggressive Fund"
        assert p.to_dict()["productType"] == "equity"
