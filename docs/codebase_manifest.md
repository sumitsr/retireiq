# RetireIQ Codebase Manifest: The Technical Map

This document provides a comprehensive directory of every Python file in the RetireIQ repository, explaining its **Purpose** and the **Architectural Approach** it follows.

---

## 🚀 1. Core Entry Points & Configuration
| File | Purpose | Approach |
|:---|:---|:---|
| `run.py` | Main application runner for development. | Simple script entry point. |
| `config.py` | Central secret management and environment loading. | Fail-fast validation (RuntimeError on missing keys). |
| `app/__init__.py` | Initializes the Flask application and extensions. | **App Factory Pattern** for test isolation. |

---

## 🌐 2. API Routes (Controllers)
Located in `app/routes/`, these files handle HTTP requests and translate them into Service calls.

| File | Purpose | Approach |
|:---|:---|:---|
| `chat.py` | Handles real-time messaging and SSE streams. | **Blueprint Pattern** with background threading. |
| `auth.py` | Manages JWT-based user login and registration. | **Stateless Auth** with `PyJWT`. |
| `profile.py` | CRUD operations for user financial and personal data. | **RESTful Resource** following ORM model. |
| `recommend.py` | Triggers the product recommendation pipeline. | **Dependency Injection** (Injects `Product` list into Service). |

---

## 🤖 3. Specialized Agents (Service Layer)
Located in `app/services/`, this is the heart of the Multi-Agent System (MAS).

| File | Purpose | Approach |
|:---|:---|:---|
| `orchestrator.py` | The "Dispatcher": Classifies intent and routes tasks. | **Semantic Router** using LLM zero-shot classification. |
| `llm_service.py` | Universal LLM adapter (OpenAI, Vertex AI, Ollama). | **Adapter Pattern** for multi-provider support. |
| `knowledge_service.py` | The "Scholar": Performs RAG and semantic search. | **Vector-Space RAG** with `pgvector` and `Vertex Embeddings`. |
| `sentinel_service.py` | Pre-trade compliance and regulatory gate. | **Rule-Engine Pattern** (Deterministic logic over LLM). |
| `vision_service.py` | Multimodal document ingestion (PDFs, Images). | **Multimodal Extraction** using Gemini 1.5 Pro. |
| `actuarial_service.py` | Monte Carlo simulations for retirement projections. | **Probabilistic Simulation** using NumPy and Life Tables. |
| `empath_service.py` | Real-time sentiment and behavioral analysis. | **Sentimental Analysis** using VADER/LLM sentiment scoring. |
| `oracle_service.py` | Real-time market data fetcher (S&P 500, inflation, yields). | **Context Injection** for real-time financial awareness. |
| `debater_service.py` | Expert Ensemble engine. | **Parallel Consensus** using 3 independent models. |
| `forensic_service.py` | Anomaly detection agent. | **Behavioral Analysis** for risk shift identification. |
| `memory_service.py` | Long-term user preference summarization. | **Recursive Summarization** for persistent context. |
| `audit_service.py` | The "Historian": Logs every agentic "Thought/Action". | **Singleton Observer** logging to PostgreSQL. |
| `sse_service.py` | Real-time server-sent events for transparent agents. | **Pub/Sub Pattern** with `threading.Lock` serialization. |
| `guardrails_service.py` | The "Shield": Filters off-topic and unsafe queries. | **Pre-flight Gatekeeper** using safety-tuned models. |
| `concierge_service.py` | Proactive alerts and scheduled milestone checks. | **Background Worker** logic for non-linear engagement. |
| `agent_service.py` | Connectivity to external bank/portfolio APIs. | **Mocked Proxy** with HMAC token derivation. |
| `recommender.py` | Logic for matching users to financial products. | **Scoring Engine** based on suitability profiles. |

---

## 🗃️ 4. Data Models (SQLAlchemy)
Located in `app/models/`, these define the relational schema.

| File | Purpose | Approach |
|:---|:---|:---|
| `user.py` | User identity and holistic financial profile. | **ORM Model** with JSON-B for semi-structured data. |
| `audit.py` | Immutable audit trail for agentic reasoning. | **WORM storage** (Write Once, Read Many) metadata. |
| `chat.py` | Conversation histories and individual messages. | **One-to-Many Relation** between Conv and Message. |
| `user_memory.py` | Permanent "Facts" extracted from conversations. | **Contextual Store** for long-term memory. |
| `product.py` | Catalog of investable retirement products. | **Static Catalog** with eligibility metadata. |
| `knowledge.py` | Chunks and metadata for the Vector database. | **Vector-Embedded Schema** for RAG retrieval. |

---

## 🛠️ 5. Utilities & Middleware
| File | Purpose | Approach |
|:---|:---|:---|
| `auth.py` | JWT verification and mandatory `@token_required`. | **Python Decorator Pattern** for AOP. |
| `pii_sanitizer.py` | The "Guardian": Anonymizes user input before LLM. | **Symmetric Proxy** (Anonymize → LLM → De-anonymize). |

---

## 🔬 6. Scripts & Test Suite
Located in `scripts/` and `tests/`.

| File | Purpose | Approach |
|:---|:---|:---|
| `seed_db.py` | Populates the database with initial test users. | Bulk insertion script. |
| `seed_knowledge.py` | Populates the Vector store with policy PDFs. | Chunking/Embedding pipeline automation. |
| `test_orchestrator.py` | Verifies intent classification logic. | **Mock-Logic Testing** (Pytest). |
| `test_pii_hardened.py` | Validates that no PII leaks to the LLM. | **Security Penetration Testing** (Regex validation). |
| `tests/conftest.py` | Shared project fixtures for Pytest. | **Fixtures Pattern** with isolated database teardown. |

---

> [!TIP]
> **Interconnection logic**: In RetireIQ, a single user message flows through:
> `Routes` → `llm_service` → `Guardian` (Anonymizer) → `Orchestrator` → `Specialist Agent` (Scholar/Actuarial) → `Historian` (Audit) → `Guardian` (De-anonymizer) → `SSE Hub` (Broadcaster).
