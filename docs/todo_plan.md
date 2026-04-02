# RetireIQ Enhancements: Master ToDo Plan

This document tracks the roadmap for evolving RetireIQ from a modular monolith to a "Bank-Grade" agentic AI ecosystem, beginning with a robust local implementation.

## Phase 1: Full-Fledged Local Core (Immediate Focus)
Goal: A fully functional backend running on high-end local hardware (Mac).
- [ ] **Local LLM Integration**: Full support for **Ollama** or local HuggingFace models (e.g., Llama 3) for offline agentic reasoning.
- [ ] **Persistent Local Storage**: Docker-Compose setup for running **PostgreSQL with pgvector** and **ChromaDB**.
- [ ] **Local PII Proxy**: Implement a robust high-performance regex/NER proxy for data redaction during local testing.
- [ ] **Agentic Isolation**: Split monolithic logic into distinct **Transaction**, **Portfolio**, **Knowledge** agents running locally.

## Phase 2: Premium UI Integration
Goal: Transform the backend into a premium, interactive user experience.
- [ ] **Frontend Initialization**: Set up a **Vite/React** or **Next.js** project with a modern dark-mode aesthetic.
- [ ] **Real-time Chat Interface**: Implement streaming responses (SSE) and robust state management for multi-turn conversations.
- [ ] **Dashboard Integration**: Build visual components for Portfolio and Transaction summaries.

## Phase 3: Demand-Based GCP Transition (Optional/Future)
Goal: Migrate to cloud-native infrastructure for enterprise scaling.
- [ ] **Vertex AI Implementation**: Swap local LLMs for Gemini 1.5 Pro and Vertex AI Vector Search.
- [ ] **Secure Architecture Deployment**: Move to Cloud Run, Cloud SQL, and Cloud DLP as envisioned in the [GCP Design Doc](system_design_gcp.md).
- [ ] **Cloud Security Hardening**: Configure Cloud Armor, IAP, and VPC Service Controls.

## Phase 4: Marketing & Evangelism
- [ ] **Animated Architecture Reveal**: Convert `gcp_architecture.png` into a ByteByteGo-style animated GIF for the LinkedIn launch.
- [ ] **GitHub README Polish**: Create a high-fidelity "Product Tour" GIF showing the local-first application in action.

---

> [!TIP]
> We are building the local application to be "Infrastructure-Agnostic," making the eventual move to GCP a simple configuration swap rather than a full rewrite.
