# Step-by-step Setup Instructions

RetireIQ is built with a **Local-First** philosophy. These instructions guide you through setting up the entire agentic ecosystem on your local machine, from a simple SQLite dev run to a full pgvector Docker deployment.

## Prerequisites
Ensure the following tools are installed:
- **Python 3.10+** and `pip`
- **Docker** and **Docker Compose**
- **Ollama** (Optional, for local LLM power — zero cloud costs)

> [!CAUTION]
> **Leak-Proof Secrets**: Ensure you never hardcode secrets. RetireIQ follows a strict [Security Strategy](./security.md) that requires all sensitive configuration to be injected via `.env`.

---

## 1. Environment Configuration

```bash
# Clone and enter the repository
cd retireiq

# Create your .env file from the template
cp .env.example .env
```

Edit `.env` with your local configuration. Key variables:

```bash
# --- Core ---
JWT_SECRET_KEY=your_super_secret_key_here

# --- LLM Provider (choose one) ---
LLM_PROVIDER=ollama              # or: azure_openai | openai | vertex_ai
LLM_MODEL_NAME=llama3            # or: gpt-4o | gemini-1.5-pro

# --- Ollama (if LLM_PROVIDER=ollama) ---
OLLAMA_HOST=http://host.docker.internal:11434

# --- Azure OpenAI (if LLM_PROVIDER=azure_openai) ---
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=

# --- Vertex AI (if LLM_PROVIDER=vertex_ai) ---
GCP_PROJECT_ID=your-gcp-project
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# --- Database ---
DATABASE_URL=sqlite:///instance/app.db   # SQLite for local dev
# DATABASE_URL=postgresql://user:pass@db:5432/retireiq  # for Docker
```

---

## 2. Quick Start (SQLite, No Docker)

Ideal for fast local development and running tests.

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install all dependencies
pip install -r requirements.txt

# Download the spaCy language model (for Presidio PII detection)
python -m spacy download en_core_web_sm

# Run the Flask development server
flask run
```

*The API will be available at `http://localhost:5000`.*

---

## 3. Full Docker Stack (PostgreSQL + pgvector)

For production-parity local development with vector search enabled.

```bash
# Set DATABASE_URL in .env to the Docker PostgreSQL service:
# DATABASE_URL=postgresql://retireiq:password@db:5432/retireiq

# Build and start all containers (API + PostgreSQL)
make up

# Monitor the logs
make logs
```

---

## 4. Local LLM Setup (Ollama — Zero Cost)

To run the full agentic pipeline without any cloud dependencies:

```bash
# Pull both models used by RetireIQ
ollama pull llama3       # General chat & reasoning
ollama pull all-minilm   # Semantic embeddings (RAG knowledge search)
```

Set your `.env`:
```bash
LLM_PROVIDER=ollama
OLLAMA_HOST=http://host.docker.internal:11434
```

> [!NOTE]
> **Troubleshooting Connectivity**: If the Docker container can't reach Ollama, set the environment variable `OLLAMA_HOST=0.0.0.0` on your host machine and restart Ollama. This allows Docker's bridge network to reach the host process.

---

## 5. Vertex AI Setup (GCP — Production)

To use Gemini 1.5 Pro/Flash with Context Caching:

1. Enable the **Vertex AI API** in your GCP project.
2. Create a service account with the `Vertex AI User` role and download the JSON key.
3. Configure `.env`:
```bash
LLM_PROVIDER=vertex_ai
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json
VERTEX_AI_MODEL_PRO=gemini-1.5-pro
VERTEX_AI_MODEL_FLASH=gemini-1.5-flash
```

---

## 6. Database Migrations & Knowledge Seeding

```bash
# 1. Apply schema migrations
flask db migrate -m "Initial schema"
flask db upgrade

# 2. Seed product catalog and user data
python scripts/seed_db.py

# 3. Seed RAG knowledge base (requires Ollama or Vertex AI for embeddings)
python scripts/seed_knowledge.py
```

---

## 7. Running Tests

```bash
# Run all 74 tests
./.venv/bin/python -m pytest

# Run with coverage report
./.venv/bin/python -m pytest --cov=app --cov-report=term-missing

# Run a specific test file
./.venv/bin/python -m pytest tests/test_orchestrator.py -v
```

> [!IMPORTANT]
> The >90% test coverage threshold must be maintained for all new features. New services must include both success and error path tests.

---

## 8. Development Utilities

```bash
# Stop all Docker containers
make down

# Access the PostgreSQL shell
make db-shell

# Verify the SSE stream is working (requires a valid token and conversation_id)
curl -N -H "Authorization: Bearer <token>" http://localhost:5000/api/chat/stream/<conversation_id>
```
