# The RetireIQ Debugging Bible: Comprehensive Troubleshooting Guide

This document is the "bible" for RetireIQ development. It captures every major technical hurdle, architectural pivot, and regression fix encountered during the build. Use this as your primary reference for future debugging and system hardening.

---

## 🐍 1. Environment & Core Architecture

### 1.1 Python 3.14 & Pydantic v2 Incompatibility
- **Issue**: Attempting to use `NeMo Guardrails` or other Pydantic-heavy libraries resulted in `InitVar` and `__future__` annotation errors.
- **Root Cause**: Python 3.14 introduced strict typing changes that broke Pydantic v2's reflective initialization.
- **The "Bible" Fix**: Pivot to the **Internal Safety Agent (The Shield)** pattern. Instead of fragile middleware, use a high-speed LLM (Gemini Flash) to perform intent-classification-as-a-guardrail.
- **Prevention**: Always use `from __future__ import annotations` and prefer internal agent logic over external guardrail libraries.

### 1.2 Circular Imports (Orchestrator vs LLM Service)
- **Issue**: `ImportError` or `AttributeError` when `orchestrator.py` and `llm_service.py` attempted to reference each other.
- **Root Cause**: Two modules requiring each other at load time.
- **The "Bible" Fix**: **Lazy Imports**. Place imports inside the specific functions (local scope) rather than at the top of the file.
- **Prevention**: Keep global singleton instances (like `dispatcher`) at the very bottom of service files.

### 1.3 Flask Background Thread Context Loss
- **Issue**: `RuntimeError: Working outside of application context` in background threads.
- **Root Cause**: Python threads do not inherit the Flask `current_app` or `db` session state.
- **The "Bible" Fix**: Pass `app.app_context()` explicitly to the thread factory and use a `with app_context:` block.
- **Prevention**: Use the pattern in `app/routes/chat.py` → `_start_agent_thread`.

---

## 🔒 2. Data Privacy & Security (The Guardian)

### 2.1 PII Placeholder Bleeding (Counter Isolation)
- **Issue**: Placeholders like `<PERSON_152>` appeared in new sessions.
- **Root Cause**: Static class variables for entity counters persisted across requests.
- **The "Bible" Fix**: Move counters to **Instance Attributes** and call `clear_mapping()` at the start of every turn.
- **Prevention**: Never store request-specific state in global or class-level variables.

### 2.2 LLM Placeholder Formatting (Regex Symmetry)
- **Issue**: De-anonymization failed because the LLM returned "Person 0" instead of `<PERSON_0>`.
- **Root Cause**: LLM "hallucinating" formatting corrections.
- **The "Bible" Fix**: 
  1. Add hard instructions to the system prompt: "DO NOT reformat placeholders."
  2. Implement fuzzy regex matchers: `(?i)<person_(\d+)>`.
- **Prevention**: Set `temperature=0.0` for sanitization tasks.

---

## ⚓ 3. Cloud & Infrastructure (GCP/Docker)

### 3.1 ADC Pathing & Service Accounts
- **Issue**: `FileNotFoundError` when the app tried to load the Google Cloud Service Account JSON.
- **Root Cause**: The file was present on the host but not volume-mounted or copied into the Docker container.
- **The "Bible" Fix**: Ensure the `.env` file uses the path *internal* to the container (e.g., `/app/certs/gcp_key.json`) and update `docker-compose.yml` to mount the certs directory.
- **Prevention**: Use `GOOGLE_APPLICATION_CREDENTIALS` environment variable instead of hardcoded paths.

### 3.2 Network Bridge (Host vs DB)
- **Issue**: `sqlalchemy` failed with `ConnectionRefusedError` for `localhost:5432`.
- **Root Cause**: Docker containers see `localhost` as themselves, not the host or other containers.
- **The "Bible" Fix**: Use the service name defined in `docker-compose.yml` (e.g., `postgresql://user:pass@db:5432/retireiq`).
- **Prevention**: Standardize on container service names in all production `.env` templates.

---

## 📚 4. RAG & Knowledge Retrieval (The Scholar)

### 4.1 Embedding Dimension Mismatch
- **Issue**: `Vector dimension mismatch (768 vs 1536)` when querying pgvector.
- **Root Cause**: Switching from local `sentence-transformers` (768) to Vertex `text-embedding-004` (1536) without re-indexing the database.
- **The "Bible" Fix**: Wipe the `knowledge_chunks` table and re-run the `ingest.py` script whenever the `EMBEDDING_MODEL` changes.
- **Prevention**: Log the expected dimension on service startup and fail-fast if the DB schema doesn't match.

### 4.2 The "Lost-in-the-Middle" Effect
- **Issue**: The Scholar found the correct PDF chunks but the LLM ignored the critical one in the middle of a long prompt.
- **Root Cause**: LLMs naturally have higher attention at the beginning and end of a context window.
- **The "Bible" Fix**: **Re-ranking**. Implement a logic that re-orders retrieved chunks so the most semantically relevant chunk is moved to the top of the prompt.
- **Prevention**: Limit retrieval to Top-K (K=3) high-fidelity chunks rather than Top-K (K=10).

---

## 📡 5. Networking & Streaming (SSE Hub)

### 5.1 Proxy Buffering (Token Stasis)
- **Issue**: Tokens only appeared in the UI all at once after a 30s delay.
- **Root Cause**: Nginx or GCP Load Balancers were buffering the HTTP response.
- **The "Bible" Fix**: Set the header `X-Accel-Buffering: no` in the Flask response and ensure `Content-Type: text/event-stream`.
- **Prevention**: Disable buffering globally for all routes under `/api/chat/stream/`.

### 5.2 Browser Connection Pool Limits
- **Issue**: Opening a 7th chat tab caused the application to "hang" for the user.
- **Root Cause**: Chrome/Firefox limit a single domain to 6 concurrent HTTP/1.1 connections. Every SSE stream takes 1 slot.
- **The "Bible" Fix**: Direct users to a single active session or implement **HTTP/2** to multiplex the streams.
- **Prevention**: Monitor active session counts per IP and proactively close stale connections.

---

## 🧪 6. Testing & Mocks

### 6.1 Multimodal Signature Regressions
- **Issue**: `tests/test_routes.py` failed after adding `attachments=None` to `generate_ai_response`.
- **Root Cause**: Mocked functions must match the signature of the real function exactly.
- **The "Bible" Fix**: Update `patch` calls to use `return_value` and ensure `**kwargs` are handled. Always patch at the **Source of Truth** (`app.services.llm_service`).
- **Prevention**: Use `autospec=True` in `pytest` mocks to catch signature mismatches early.

---

## 🗳️ 7. Multi-Model Ensemble Reasoning (The Debater)

### 7.1 Case #11: The Outlier Authority (Ensemble Discrepancy)
- **Issue**: The Debater returns a "Low Consensus Confidence" score or Model B (GPT) disagrees with Model A (Gemini).
- **Root Cause**: Models have different "Domain Authorities." GPT is superior at logic/math; Gemini is superior at policy RAG.
- **The "Bible" Fix**: Implement a **Weighted Moderator**. Explicitly brief the Moderator LLM on the `DOMAIN_AUTHORITY` weight matrix. If the "Authority" model is the minority, flag a **"Critical Discrepancy"** for human forensic review.
- **Prevention**: Always log the Moderator's "Thought" process to see why one expert was prioritized over another.

### 7.2 Case #12: Threading Timeouts (The 20-Second Wall)
- **Issue**: The Debater returns a partial response or fails to gather all 3 viewpoints.
- **Root Cause**: One endpoint (usually local Ollama or slow Azure regions) took longer than the 20-second `t.join(timeout=20)` limit.
- **The "Bible" Fix**: Increase the join timeout or implement a **Streaming Async Debater** that processes whichever results arrive first.
- **Prevention**: Monitor `[Debater] Model X failed` in the Historian logs to identify slow providers.

---

> [!IMPORTANT]
> **Final Word**: This bible is a living document. Whenever a new "WTF" moment occurs, document it here. The goal is to ensure that no developer has to solve the same obscure bug twice.
