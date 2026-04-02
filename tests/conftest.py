import pytest
from app import create_app, db
from app.models.user import User
from app.models.product import Product

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test_key"
    JWT_SECRET = "test_jwt_secret"
    OPENAI_API_KEY = "dummy-key"
    ANTHROPIC_API_KEY = "dummy-key"

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def seed_data(app):
    with app.app_context():
        user = User(
            id="test_user_id",
            email="test@user.com",
            first_name="Test",
            last_name="User",
            financial_profile={"totalAssets": 100000.0},
            password_hash="fakehash"
        )
        db.session.add(user)
        
        prod = Product(
            id="test_prod_1",
            name="Test Aggressive Fund",
            type="equity",
            risk_level="high",
            data={"category": "equity"}
        )
        db.session.add(prod)
        db.session.commit()
        yield {"user_id": "test_user_id", "product_id": "test_prod_1"}
