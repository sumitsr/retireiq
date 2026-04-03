# RetireIQ Enhancements: Strategic ToDo Plan

This document tracks the technical execution of RetireIQ's evolution, focusing on a robust local foundation and premium user experience.

---

## Phase 1: Full-Fledged Local Core (Immediate Focus)
**The Why**: To build a "Bank-Grade" system, we must have environment parity and local vector storage. Docker ensures our app runs identical environments anywhere, and `pgvector` unlocks the semantic retrieval required for sophisticated RAG.

- [x] **Establish Leak-Proof Secrets Management**: 
  - **How**: Implemented `${VARIABLE}` interpolation in `docker-compose.yml` and a "Fail-Fast" `RuntimeError` in `config.py` if mandatory keys are missing.
- [x] **Local LLM Integration (Ollama)**:
  - **How**: Implemented `call_ollama_api` in `llm_service.py` to support zero-cost development using the local Ollama host bridge.
- [ ] **Persistent Local Storage**:
  - **Why**: Ensure financial data and vector embeddings persist across container restarts.
  - **How**: Docker-Compose setup for running **PostgreSQL with pgvector** and **ChromaDB**.
- [ ] **Local PII Proxy**:
  - **Why**: Security must be proactive. We need to mask sensitive data *before* it leaves our internal service boundary.
  - **How**: Integrate **Microsoft Presidio** or high-performance regex logic for real-time redaction.

---

## Phase 2: Agentic Intelligence (The "Long Vision")
**The Why**: A monolithic AI service is limited. Specialized agents handle complex domains better, ensuring higher accuracy and safer operations for financial transactions.

- [ ] **Intent Resolution Engine**:
  - **How**: Develop a **Semantic Router** using Gemini 1.5 Flash to classify user prompts into "Trade," "Knowledge," or "Portfolio" intents.
- [ ] **Multi-Agent Isolation**:
  - **How**: Split logic into distinct services (**Transaction**, **Portfolio**, **Knowledge**) with their own "Tools" (functions) they can invoke.
  - **High-Fidelity Agent Audit Trail**: Implement a centralized **Audit Sentinel** that records every agent decision, tool call, and reasoning step against a `SessionID`. This provides the "Black Box" transparency required for bank-grade financial operations.
  - **Automated Portfolio Reporting**: Enable the **Portfolio Agent** to generate high-fidelity PDF summaries of user recommendations (using **WeasyPrint** or **ReportLab**) and deliver them via secure email (SMTP/Flask-Mail) if requested.
- [ ] **Stateful Conversational Memory**:
  - **Why**: The system must "learn" user preferences (risk tolerance, goals) to provide truly personalized advice.
  - **How**: Migrate session memory to **Cloud Firestore** or persistent relational models.

---

## Phase 3: Premium UI Integration
**The Why**: A high-impact product needs a visual layer that matches the backend's complexity. Real-time interaction (SSE) and modern design are non-negotiable for customer trust.

- [ ] **Frontend Initialization**: 
  - **How**: Set up a **Next.js** or **Vite/React** project with a unified dark-mode design system.
- [ ] **Real-time Interaction (SSE)**:
  - **How**: Implement Server-Sent Events (SSE) to stream agentic "Chain of Thought" and final responses for a smooth UX.

---

## Phase 4: Optional GCP Transition (Enterprise Ready)
**The Why**: Once the local core is "Bank-Grade," we can offer a cloud-native setup for security, cost-optimization at scale, and global availability.

- [ ] **Vertex AI Integration**: Swap local LLMs for Gemini 1.5 Pro and Vertex AI Vector Search.
- [ ] **Secure Architecture Deployment**: Move to **Cloud Run** and **Cloud SQL** (as mapped in the [GCP Design Doc](system_design_gcp.md)).

---

## Phase 5: Marketing & Evangelism
- [ ] **Animated Architecture Reveal**: High-impact visuals using **Eraser.io** for the LinkedIn launch.
- [ ] **GitHub README Polish**: Premium "Product Tour" showcase.

---

## Phase 6: The Autonomous Guardian (Best-of-Kind)
**The Why**: To reach the "Pinnacle" of AI financial assistants, the system must move beyond being reactive. It must anticipate needs, contextualize market movements, and analyze non-textual data (like photo statements).

- [ ] **Proactive Nudging & Market Oracle**:
  - **Why**: Prevent missed opportunities (e.g. tax-loss harvesting).
  - **How**: Background workers that monitor the portfolio and market feeds, triggering the **Oracle Agent** to suggest actions.
- [ ] **Multi-Modal Statement Ingestion**:
  - **Why**: Manual data entry is a friction point.
  - **How**: Deploy a **Vision Agent** to OCR and ingest competitor PDF/image statements into the relational model.
- [ ] **Empathy & Sentiment Alignment**:
  - **Why**: Financial decisions are emotional. 
  - **How**: Integrate a **Sentiment Agent** to detect stress/urgency and dynamically adjust the LLM's system prompt tone.

---

> [!TIP]
> This roadmap is modular. We focus on Phase 1 & 2 to ensure we have a functional local product before worrying about cloud deployments.
