import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, "instance")


class Config:
    # Mandatory Security Settings (Application will fail-fast if these are missing)
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY environment variable is not set!")

    # Defaulting to sqlite if no DB url is provided
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(
        instance_path, "app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LLM Settings
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")
    LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "llama3")
    LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
