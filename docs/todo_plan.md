# RetireIQ Enhancements: Strategic ToDo Plan

This document tracks the technical execution of RetireIQ's evolution, focusing on a robust local foundation and premium user experience.

> [!NOTE]
> **Last updated after Phase 4 completion.** Phases 1–4 are complete and verified with 74 passing tests. Phases 5–7 represent the roadmap toward a fully autonomous, bank-grade AI financial platform.

---

## Phase 1: Full-Fledged Local Core ✅ COMPLETE

- [x] **Leak-Proof Secrets Management**: Fail-fast `RuntimeError` in `config.py`, `${VARIABLE}` interpolation in docker-compose.
- [x] **Local LLM Integration (Ollama)**: `call_ollama_api` in `llm_service.py` for zero-cost local dev.
- [x] **Bank-Grade PII Proxy**: Microsoft Presidio with custom `SSN` + `ACCOUNT_NUMBER` recognizers. Full anonymise → LLM → de-anonymise cycle.
- [x] **95%+ Test Coverage (74 tests passing)**: Suites for memory, profile, recommend, llm_service, orchestrator, sse_service, vertex_service.

---

## Phase 2: Agentic Intelligence ✅ COMPLETE

- [x] **Intent Resolution Engine (Dispatcher Agent)**: Semantic Router in `orchestrator.py` (Gemini Flash, T=0.0). Classifies: `KNOWLEDGE_BASE`, `PORTFOLIO_ANALYSIS`, `TRANSACTIONAL`, `GENERAL`.
- [x] **Multi-Agent Isolation**: Scholar (RAG), Analyst (Portfolio), Executor (Trade) — each with its own context boundary.
- [x] **High-Fidelity Audit Trail (The Historian)**: `AgentAudit` model + `audit_service.py`. Every THOUGHT, ACTION, OBSERVATION, RESPONSE persisted with `session_id`.
- [x] **Stateful Conversational Memory**: Background `summarize_into_facts` extracting long-term preferences into `UserMemory`.

---

## Phase 3: Real-time Interaction (SSE) ✅ COMPLETE

- [x] **SSE Hub (Stream Dispatcher)**: Thread-safe `SSEService` per `session_id`. Broadcasts `agent_step`, `final_response`, and `ping` events.
- [x] **Historian → SSE Integration**: Every `log_step()` simultaneously writes to DB and publishes to the SSE stream.
- [x] **API Gateway Upgrade**: `GET /api/chat/stream/<id>` + async `POST /api/chat/message` returning 202.

---

## Phase 4: GCP & Vertex AI Transition ✅ COMPLETE

- [x] **Vertex AI Integration**: `call_vertex_ai_api()` using `google-cloud-aiplatform` SDK.
- [x] **Model Tiering**: Gemini Flash for dispatching, Gemini Pro for deep reasoning.
- [x] **Context Caching**: `VertexCacheManager.create_policy_cache()` — up to 90% token reduction for repeated Scholar queries.
- [x] **Vertex AI Embeddings**: `text-embedding-004` for enterprise-grade RAG.

---

## Phase 5: Refactor & Production Hardening ✅ COMPLETE

- [x] **Big Function Refactors**: Every large function decomposed into single-responsibility helpers across `llm_service`, `orchestrator`, `chat`, `memory_service`, `sse_service`, `pii_sanitizer`.
- [x] **Structured Logging**: Module-level `logger = logging.getLogger(__name__)` everywhere. All `print()` replaced with `logger.info/debug/warning/error(exc_info=True)`.
- [x] **Documentation Overhaul**: `architecture.md`, `evolution_timeline.md`, `sequence-diagrams.md`, `security.md`, `setup-instructions.md` fully updated.
- [x] **AI & Python Masterclasses**: 12 AI modules + 10 Python modules. All stubs filled with expert-level content, code examples, and RetireIQ rationale.

---

## Phase 6: Marketing & Evangelism 📅 PLANNED

- [ ] **Animated Architecture Reveal**: High-impact visuals using Eraser.io for LinkedIn launch.
- [ ] **GitHub README Polish**: Premium "Product Tour" showcase with architecture GIF.
- [ ] **Frontend Dashboard (Next.js/React)**: Dark-mode UI with real-time SSE Chain-of-Thought panel.

---

## Phase 7: The Autonomous Agent Ecosystem 📅 FUTURE ROADMAP

This phase elevates RetireIQ from a reactive Q&A system to a fully autonomous, proactive, and enterprise-regulated financial intelligence platform.

### 🔴 Priority 1 — Regulatory & Core Differentiation (Must-have)

#### The Sentinel (Pre-Trade Compliance Agent)
- **Why**: Without a pre-trade rules engine, RetireIQ cannot legally execute financial transactions under FCA/FINRA regulation.
- **How**: Every TRANSACTIONAL intent passes through the Sentinel before the Executor. Returns PASS / WARN / BLOCK with a compliance reasoning trail persisted to `AgentAudit`.
- **Stack**: Rules Engine (Python dict), AML API (ComplyAdvantage / Refinitiv), compliance policy database.

#### The Actuarial (Monte Carlo Simulation Agent)
- **Why**: Answers the most critical retirement question: *"Will I actually have enough money?"* — accounting for market volatility, inflation, and longevity risk.
- **How**: 10,000+ scenario simulations using log-normal return sampling. Outputs probabilistic success rates (e.g., "78% chance of not outliving savings to age 90").
- **Stack**: NumPy (simulations), SciPy (statistical distributions), Plotly (confidence band visualisations), actuarial life tables.

---

### 🟡 Priority 2 — User Experience & Retention (High Value)

#### The Vision (Document Ingestion Agent)
- **Why**: Collapses 2-hour manual financial onboarding into 2 minutes by reading uploaded pension statements, P60s, and ISA summaries automatically.
- **How**: OCR via Google Document AI / Tesseract. Gemini 1.5 Pro parses and normalises extracted data into the RetireIQ schema. Guardian Agent scrubs PII before storage.
- **Stack**: Google Document AI, Pillow (image preprocessing), Gemini 1.5 Pro (long-context extraction).

#### The Empath (Behavioral Finance Agent)
- **Why**: Irrational behavioral biases (panic selling, FOMO) destroy more retirement savings than poor market selection. No current AI retirement product addresses this.
- **How**: Real-time sentiment analysis on every user message. Detects panic/FOMO signals and dynamically adjusts the LLM system prompt tone.
- **Stack**: VADER Sentiment / Gemini Flash, rule-based bias detector, dynamic system prompt injection.

#### The Concierge (Proactive Outreach Agent)
- **Why**: A true financial advisor doesn't wait. Tax deadlines, ISA resets, RMD dates — these pass silently and cost users money.
- **How**: Personalised event calendar per user. Scheduled background scan for upcoming financial deadlines triggers proactive SSE/email/SMS alerts.
- **Stack**: APScheduler, personalised event store (PostgreSQL), SendGrid (email), Twilio (SMS).

---

### 🟢 Priority 3 — Enterprise & Strategic (Long-term)

#### The Oracle (Market Intelligence Agent)
- **Why**: RetireIQ currently has no awareness of the real world. Market events actively eroding a user's portfolio should trigger proactive alerts.
- **How**: Real-time market data feeds (yfinance, Alpha Vantage). Cross-references user holdings for price/news thresholds. Feeds the Concierge with alert triggers.
- **Stack**: APScheduler, yfinance / Alpha Vantage, Gemini Flash (news summarisation), Celery (task queue).

#### The Debater (Ensemble Reasoning Agent)
- **Why**: For high-stakes decisions (>20% portfolio impact), a single model's error is catastrophic. Investment committees never let one analyst make a large call alone.
- **How**: Spawns 3 independent agents (different models + perspectives: bull / bear / neutral). A Moderator Agent synthesises the responses and quantifies uncertainty.
- **Stack**: Python threading (parallel agents), Gemini Pro + GPT-4o + Llama3, consensus scoring logic.

#### The Forensic (Fraud Detection Agent)
- **Why**: A platform that executes transactions is a fraud target. Unusual transaction velocity, geo-location changes, and trade-size anomalies need to be caught before execution.
- **How**: ML-based anomaly detection (Isolation Forest) on transaction features. High-risk events trigger human review via webhook and block the transaction pending verification.
- **Stack**: scikit-learn (Isolation Forest), GeoIP2 (location), Redis (velocity tracking), PagerDuty API.

---

> [!TIP]
> The Phase 7 agents follow the same architectural patterns established in Phases 2–4: each agent uses the Historian for audit logging, publishes to the SSE stream, and is tested with the Mock-First pattern. The infrastructure is already in place — these are domain-specific extensions, not architectural rebuilds.
