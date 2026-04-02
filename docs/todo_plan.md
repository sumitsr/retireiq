# RetireIQ Enhancements: Master ToDo Plan

This document tracks the roadmap for evolving RetireIQ from a modular monolith to a "Bank-Grade" agentic AI ecosystem on Google Cloud Platform.

## Phase 0: Local-First "Development Flavor" (Coming Soon)
- [ ] **Local LLM Integration**: Support for **Ollama** or local HuggingFace models for offline testing.
- [ ] **Local Discovery**: Docker-Compose setup for running the ChatRouter, PII-proxy, and Vector DB (ChromaDB/PostgreSQL) on a single machine.
- [ ] **Mocked Security Services**: Simplified local PII redaction using high-performance regex (no Cloud DLP dependency needed for dev).

## Phase 1: Core AI Infrastructure (GCP Foundation)
- [ ] **Vector Database Provisioning**:
  - [x] Select between Vertex AI Vector Search (High scale) and Cloud SQL/AlloyDB with `pgvector` (Balanced cost).
  - [ ] Implement consistent embedding logic (Vertex AI `text-multilingual-embedding-002`).
- [ ] **Knowledge Base Ingestion**:
  - [ ] Build a Cloud Storage (GCS) trigger for document ingestion (PDFs/Policy documents).
  - [ ] Implement a Cloud Dataflow or Cloud Run ingestion pipeline for chunking and upserting to the Vector DB.
- [ ] **PII Sanitization Gateway**:
  - [ ] Deploy the "Security Firewall" (Cloud Run proxy).
  - [ ] Integrate Google Cloud Sensitive Data Protection (DLP) API for complex redaction.
  - [ ] Implement the ephemeral re-hydration map logic.

## Phase 2: Agentic Orchestration & Intelligence
- [ ] **Intent Resolution Engine**:
  - [ ] Develop a semantic router (Fast, low-latency) to classify user prompts into agent types.
  - [ ] Integrate **Gemini 1.5 Flash** as the high-speed classifier.
- [ ] **Multi-Agent Isolation**:
  - [ ] **Knowledge Agent**: Dedicated RAG-powered agent for policy queries.
  - [ ] **Portfolio Agent**: Logic to safely query balances and holdings via the SQLAlchemy ORM.
  - [ ] **Transaction Agent**: Secure logic for initiating retirement account movements.
- [ ] **Stateful Conversational Memory**:
  - [ ] Migrate memory from local state/JSON to **Cloud Firestore** or **Cloud SQL**.
  - [ ] Evolve memory into a "Learning Profile" that extracts and saves user traits/risk tolerance long-term.

## Phase 3: Enterprise Polish & Production Readiness
- [ ] **Observability Stack**:
  - [ ] Configure Cloud Trace across orchestrator and task agents to debug multi-step AI reasoning.
  - [ ] Set up Cloud Monitoring dashboards for LLM latency, token usage, and cost monitoring.
- [ ] **Cost Optimization Implementation**:
  - [ ] Enable **Vertex AI Context Caching** for policy documents to reduce input token overhead.
  - [ ] Implement the "Hybrid Redaction" logic (Local Regex -> Cloud DLP) to minimize security API costs.
- [ ] **Security Hardening**:
  - [ ] Configure **Cloud Armor** WAF rules for the API Gateway.
  - [ ] Lock down infrastructure using identity-aware proxy (IAP) and VPC Service Controls.

## Phase 4: Marketing & Evangelism
- [ ] **Animated Architecture Reveal**: Convert `gcp_architecture.png` into a ByteByteGo-style animated GIF using Eraser.io for the LinkedIn launch.
- [ ] **GitHub README Polish**: Create a high-fidelity "Product Tour" GIF showing the local-first flavor in action.

---

> [!TIP]
> This plan is modular. You can start with **Phase 1** to get a functional RAG system before moving to the multi-agent orchestration in **Phase 2**.
