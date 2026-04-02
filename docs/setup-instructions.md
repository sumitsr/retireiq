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
```

## 5. Development Utilities

```bash
# Run unit tests
pytest tests/

# Check styling and lints
ruff check .
```
