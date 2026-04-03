# Step-by-step Setup Instructions

RetireIQ is built with a **Local-First** philosophy. These instructions guide you through setting up the entire agentic ecosystem on your local machine using Docker.

## Prerequisites
Ensure the following tools are installed:
- **Docker** and **Docker Compose**
- **Make** (for shorthand commands)
- **Ollama** (Optional, for local LLM power)

> [!CAUTION]
> **Leak-Proof Secrets**: Ensure you never hardcode secrets. RetireIQ follows a strict [Security Strategy](../docs/security.md) that requires all sensitive data to be injected via `.env`.

---

## 1. Environment Configuration
First, prepare your environment variables for the Dockerized services.

```bash
# Clone and enter the repository
cd retireiq

# Create your .env file
cp .env.example .env
```

Open `.env` and set your local configuration. For Docker usage, use the service name `db` for the database host.

---

## 2. Launching the Local Core
We use `docker-compose` to spin up the API and the PostgreSQL (with pgvector) database simultaneously.

```bash
# Build and start the containers
make up

# Monitor the logs
make logs
```
*The API will be available at `http://localhost:5000`.*

---

## 3. Local LLM Setup (Ollama)
To run the agentic logic without cloud dependencies:
1. Install [Ollama](https://ollama.com/).
2. Pull the required models:
   ```bash
   ollama pull llama3       # For reasoning/chat
   ollama pull all-minilm  # For semantic embeddings (RAG)
   ```
3. Configure your `.env` to use the local provider:
   ```bash
   LLM_PROVIDER=ollama
   LLM_MODEL_NAME=llama3
   OLLAMA_HOST=http://host.docker.internal:11434
   ```

### 🛡️ Ollama Connectivity (Troubleshooting)
If the API container says it "Encountered an error with the local Ollama service":
- **macOS/Windows**: Ensure Ollama is running and that you have restarted it *after* setting up Docker.
- **Environment Variable**: You may need to set `OLLAMA_HOST=0.0.0.0` in your host environment and restart Ollama to ensure it accepts connections from the Docker network bridge.

---

## 4. Database Migrations & Knowledge Seeding
Once the containers are running, apply the latest relational schemas and seed the vector database.

```bash
# 1. Run migrations for new tables (e.g. knowledge_chunks)
docker exec -it retireiq_app flask db migrate -m "Add knowledge chunks"
docker exec -it retireiq_app flask db upgrade

# 2. Seed binary/relational data (Products & Users)
docker exec -it retireiq_app python scripts/seed_db.py

# 3. Seed semantic knowledge (RAG Policies)
# Note: Ensure Ollama is running and has 'all-minilm' pulled
docker exec -it retireiq_app python scripts/seed_knowledge.py
```

---

## 5. Knowledge Management (RAG)
To maintain the "Scholar" persona's intelligence:
- **Adding Documents**: Use the `KnowledgeService` to ingest new PDFs or text policies.
- **Verification**: You can verify semantic retrieval by running `db-shell` and querying the `knowledge_chunks` table directly.

---

## 5. Development Utilities
Use these shorthands for daily development:

```bash
# Stop the environment
make down

# Access the Database shell
make db-shell

# Run unit tests
pytest tests/
```
