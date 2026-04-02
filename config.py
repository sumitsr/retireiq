import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, "instance")


class Config:
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    # Defaulting to sqlite if no DB url is provided
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(
        instance_path, "app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LLM Settings
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
    LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gpt-4o")
    LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
