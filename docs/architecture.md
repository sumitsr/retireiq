# RetireIQ Backend Architecture

RetireIQ is a "Bank-Grade" retirement planning assistant built on a production-grade Multi-Agent System (MAS). It uses a Dispatcher/Orchestrator pattern with specialized agents for knowledge retrieval, portfolio analysis, and financial transactions — all backed by a granular Audit Sentinel ("The Historian") for full transparency.

---

## Current Architecture: The Autonomous Agent Ecosystem

RetireIQ now operates as a high-fidelity **Agentic Ecosystem**. Every user message passes through a multi-layered security, safety, and behavioral pipeline before reaching a specialist agent.

```mermaid
graph TD
    Client["Client / Web / Mobile"] -->|POST /api/chat/message| API["Flask API Gateway"]
    Client -->|GET /api/chat/stream/:id| SSE["SSE Stream Dispatcher"]

    subgraph "Behavioral Layer (The Empath)"
        API --> Empath["Empath Agent\n(Sentiment → Tone Adjustment)"]
    end

    subgraph "Security Boundary (The Guardian)"
        Empath --> PII["PII Sanitizer (Presidio)\nAnonymize → LLM → De-anonymize"]
    end

    subgraph "Safety Layer (The Shield)"
        PII --> Shield["Shield Agent (Guardrails)\nOff-topic / Jailbreak Filter"]
    end

    subgraph "Orchestration Layer"
        Shield --> Dispatcher["Dispatcher Agent (Router)"]
        Dispatcher -->|KNOWLEDGE_BASE| Scholar["Scholar Agent (RAG)"]
        Dispatcher -->|TRANSACTIONAL| Sentinel["Sentinel (Compliance Gate)"]
        Dispatcher -->|RETIREMENT_SIM| Actuarial["Actuarial Agent (Monte Carlo)"]
        Dispatcher -->|PORTFOLIO_ANALYSIS| Analyst["Analyst Agent (Recommender)"]
        Dispatcher -->|GENERAL| Fallback["General LLM (Pro/Flash/Local)"]
    end

    subgraph "Execution & Compliance"
        Sentinel -->|PASS| Executor["Executor Agent"]
        Vision["Vision Agent (OCR)"] -->|Structured Data| Scholar
    end

    subgraph "Audit & Observation"
        Dispatcher --> Historian["Historian (AgentAudit DB)\nTHOUGHT → ACTION → OBSERVATION"]
        Scholar --> Historian
        Historian --> SSE
    end
```

---

## Future Architecture: The Autonomous Agent Ecosystem (Phase 7)

The current architecture covers the **reactive** dimension. The Phase 7 agents add **proactive**, **preventive**, and **predictive** dimensions.

```mermaid
graph TD
    Client["Client / Web / Mobile"]
    Concierge["🗓 Concierge Agent\nProactive Outreach"]
    Oracle["🔮 Oracle Agent\nMarket Intelligence"]
    Empath["🧠 Empath Agent\nBehavioral Finance"]

    subgraph "Proactive Layer (Phase 7)"
        Oracle --> Concierge
        Concierge -->|SSE / Email / SMS| Client
    end

    Client -->|POST /api/chat/message| API["Flask API Gateway"]
    API --> Empath
    Empath -->|Tone Adjustment| Dispatcher

    subgraph "Orchestration Layer"
        Dispatcher["Dispatcher Agent (Router)"]
        Dispatcher -->|KNOWLEDGE_BASE| Scholar["Scholar Agent (RAG)"]
        Dispatcher -->|TRANSACTIONAL| Sentinel
        Dispatcher -->|PORTFOLIO_ANALYSIS| Actuarial
        Dispatcher -->|GENERAL| Fallback["General LLM"]
    end

    subgraph "Safety & Compliance Layer"
        Sentinel["⚖️ Sentinel Agent\nPre-Trade Compliance"] -->|PASS| Executor["Executor Agent"]
        Sentinel -->|BLOCK| Forensic["🕵️ Forensic Agent\nFraud Detection"]
    end

    subgraph "Intelligence Layer"
        Actuarial["📊 Actuarial Agent\nMonte Carlo Simulation"]
        Vision["🧾 Vision Agent\nDocument Ingestion / OCR"]
        Vision -->|Structured Data| Scholar
    end

    subgraph "High-Stakes Safety"
        Actuarial -->|High Impact?| Forensic["🕵️ Forensic Agent\nAnomaly Detection"]
        Forensic -->|Anomalous?| Debater["🗳 Debater Agent\nExpert Ensemble (3× Model)"]
    end

    subgraph "Historian & Stream"
        Historian["Historian (Audit DB)"]
        SSE["SSE Stream Dispatcher"]
        Historian --> SSE
    end
```

---

## Core Components (Current)

### 1. Flask App Factory (`app/__init__.py`)
Modular monolith using Blueprints. Registers all SQLAlchemy models (including `AgentAudit`) at startup.

### 2. Orchestrator / Dispatcher (`app/services/orchestrator.py`)
The central nervous system. Uses Gemini Flash (T=0.0) to classify user intent into domains, then delegates to specialists via `_classify_intent` → `_parse_intent_response` → `_route`.

### 3. Historian / Audit Sentinel (`app/services/audit_service.py` + `app/models/audit.py`)
Every agentic step is persisted with `session_id`, `agent_name`, `step_type` (THOUGHT/ACTION/OBSERVATION/RESPONSE), and `content`.

### 4. Stream Dispatcher / SSE Hub (`app/services/sse_service.py`)
Thread-safe event hub. All Historian log steps simultaneously broadcast to the client's SSE stream. Heartbeat pings every 20s prevent proxy timeouts.

### 5. PII Sanitization Gateway (`app/utils/pii_sanitizer.py`)
Bank-grade proxy using Microsoft Presidio. Custom recognizers for `SSN` and `ACCOUNT_NUMBER`. Symmetric: anonymise → LLM → de-anonymise (the "Ghost Map" pattern). Session-isolated via `clear_mapping()`.

### 6. Knowledge Service (`app/services/knowledge_service.py`)
Semantic search via `pgvector` (local) or Vertex AI `text-embedding-004` (cloud). Includes `VertexCacheManager` for 90% input token reduction on repeated large policy lookups.

### 7. Memory Service (`app/services/memory_service.py`)
Background fact extraction from conversation history into `UserMemory`. Runs in a daemon thread after each conversation turn.

---

## Status of Autonomous Agents

| Agent | Role | Status | Pattern |
|-------|------|--------|---------|
| **Guardian** | PII Sanitization (Presidio) | ✅ Delivered | Request Proxy |
| **Shield** | Conversational Guardrails (Safety) | ✅ Delivered | Intent Filter |
| **Sentinel** | Pre-trade compliance & rules engine | ✅ Delivered | Pre-Executor filter |
| **Actuarial** | Monte Carlo retirement success simulation | ✅ Delivered | Compute background task |
| **Vision** | OCR & document ingestion (Statements) | ✅ Delivered | Multimodal Extraction |
| **Empath** | Behavioral finance sentiment analysis | ✅ Delivered | Pre-Dispatcher Layer |
| **Concierge** | Proactive outreach & scheduling | ✅ Delivered | SSE / Task Skeleton |
| **Oracle** | Real-time market intelligence | ✅ Delivered | Market data feeds |
| **Debater** | Expert Ensemble (3× Weighted Models) | ✅ Delivered | Expert Weighting Logic |
| **Forensic** | Fraud detection & anomaly scoring | ✅ Delivered | Velocity tracking |

---

## Data Models

| Model | Table | Purpose |
|-------|-------|---------|
| `User` | `users` | Core profile, financial data, preferences |
| `Conversation` | `conversations` | Groups messages by session |
| `Message` | `messages` | Individual user/bot turns |
| `UserMemory` | `user_memory` | Long-term extracted facts |
| `KnowledgeChunk` | `knowledge_chunks` | RAG document store + embeddings |
| `Product` | `products` | Financial product catalog |
| **`AgentAudit`** | **`agent_audit`** | **High-fidelity agentic audit trail** |

---

## Provider Switching

| `LLM_PROVIDER` | Model | Use Case |
|----------------|-------|---------|
| `vertex_ai` | Gemini 1.5 Pro/Flash | Production (GCP) |
| `azure_openai` | GPT-4o | Enterprise (Azure, PCI DSS) |
| `openai` | GPT-4o | Cloud (OpenAI) |
| `ollama` | Llama3 | Local Dev (Zero Cost) |
