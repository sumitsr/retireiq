from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import Config
import logging

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    db.init_app(app)

    # Register models
    from app.models.user import User
    from app.models.chat import ChatMessage
    from app.models.knowledge import KnowledgeChunk

    # Set up basic logging
    logging.basicConfig(level=logging.INFO)

    # Register blueprints (we will import these after setting up routes)
    from app.routes.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.routes.profile import bp as profile_bp

    app.register_blueprint(profile_bp, url_prefix="/api/profile")

    from app.routes.chat import bp as chat_bp

    app.register_blueprint(chat_bp, url_prefix="/api/chat")

    from app.routes.recommend import bp as recommend_bp

    app.register_blueprint(recommend_bp, url_prefix="/api/recommend")

    # We will also need unauth route endpoints mapped
    # They are included in profile and recommend respectively.
    # To keep exact /api/unauth endpoints, we will map them directly on app if needed or rely on the blueprint prefixes.
    # Currently they are defined inside profile.py and recommend.py with /unauth.
    # To match frontend /api/unauth/profile:
    from app.routes.profile import get_profile_unauth
    from app.routes.recommend import get_recommendation_unauth

    app.add_url_rule("/api/unauth/profile", view_func=get_profile_unauth, methods=["GET"])
    app.add_url_rule("/api/unauth/recommend", view_func=get_recommendation_unauth, methods=["GET"])

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy"}

    return app
