# Security and Compliance Blueprint: Bank-Grade Agentic Ecosystem

This document details the multi-layered security and compliance measures implemented within RetireIQ to meet stringent financial regulatory standards (FCA, FINRA, GDPR, and MiFID II).

---

## 🛡️ 1. Layered Defense-in-Depth Architecture

RetireIQ employs a three-layer security model to protect user data and ensure regulatory compliance.

### Layer 1: The Privacy Layer (The Guardian)
*   **Component**: `app/utils/pii_sanitizer.py`
*   **Technology**: **Microsoft Presidio** + Custom Financial Recognizers.
*   **Mechanism**: Symmetric Anonymization (The "Ghost Map").
*   **Function**: Redacts PII (Names, Emails, Phones) and sensitive financial identifiers (IBANs, UK National Insurance Numbers) **locally** before any data is sent to external LLM providers (Gemini/Azure/Ollama).
*   **Isolation**: PII mappings are request-scoped and never persisted to logs or databases.

### Layer 2: The Safety Layer (The Shield)
*   **Component**: `app/services/guardrails_service.py`
*   **Technology**: **Internal Safety Agent** (based on Gemini Flash).
*   **Function**: A high-speed conversational gate that classifies user intent for:
    *   **Off-Topic Steering**: Blocking non-financial queries (e.g., medical advice, coding help).
    *   **Jailbreak Detection**: Identifying prompt injection attempts to bypass persona.
    *   **Self-Harm/Policy Violations**: Ensuring the AI never generates unsafe content.
*   **Deterministic Fallback**: If "The Shield" detects a violation, it triggers a pre-defined refusal response, bypassing the specialist agents entirely.

### Layer 3: The Regulatory Layer (The Sentinel)
*   **Component**: `app/services/sentinel_service.py`
*   **Mechanism**: Deterministic Python Logic (Hard Rules).
*   **Function**: Enforces financial "Hard-Stops" before any trade or advice is finalized:
    *   **Suitability (MiFID II)**: Validates that asset risk matches the user's risk tolerance.
    *   **Concentration Limit**: Blocks trades that would result in >10% allocation in a single stock.
    *   **Age-Based Drawdown**: Prevents pension withdrawals if the user is under 55 (UK regulation).
*   **Security Rationale**: Rules are coded in Python, making them immune to LLM prompt injection or hallucinations.

---

## 🏛️ 2. Regulatory Alignment Mapping

| Requirement | Measure Taken | Implementation Component |
| :--- | :--- | :--- |
| **GDPR Privacy** | Privacy-by-Design / Data Minimization | **PIISanitizer** (Presidio + Ghost Map) |
| **MiFID II Suitability** | Investor Protection / Suitability Check | **The Sentinel** (SuitabilityRule + Risk Profile) |
| **SEC 17a-4 / FINRA** | Immutable Recordkeeping / Books & Records | **AuditService** (The Historian, 7-yr persistence) |
| **FCA Consumer Duty** | Foreseeable Harm Prevention / Sludge-Detect | **The Shield** (Outcome-based Filtering) |

---

## 🔑 3. Access Control & Least Privilege

### 3.1 Session-Limited Tokens (HMAC)
When RetireIQ calls external Specialist Agents, it does not use a master API key. Instead, it generates a **Short-Lived Session Token** (`agent_service.py`):
1.  A token is derived using **HMAC-SHA256** from a master secret and the current `conversation_id`.
2.  The token is only valid for that specific session.
3.  This prevents "Session Hijacking" where one agent call could theoretically access another user's context.

### 3.2 System Hardening
*   **Environment Variables**: All secrets (JWT, GCP, Azure) are injected at runtime.
*   **Fail-Fast Config**: The application crashes immediately on startup if mandatory security keys are missing.
*   **Source Integrity**: `.env` and sensitive logs are strictly excluded via `.gitignore`.

---

## 📈 4. Auditability & Explainability (The Historian)

Every interaction within the ecosystem generates a structured audit trail in the `agent_audit` table:
*   **THOUGHT**: The model's internal reasoning (Chain-of-Thought).
*   **ACTION**: The specific tool call or API request made.
*   **OBSERVATION**: The raw data returned by a tool (e.g., stock price).
*   **RESPONSE**: The final grounded message sent to the user.

> [!TIP]
> **Audit Retention**: In production, these records are archived for **7 years** on immutable (WORM) storage to satisfy SEC/FCA requirements.

---

## 🏛️ 5. FCA (UK) Compliance: The Consumer Duty Focus

For a Solution Architect, FCA compliance centers on **Outcome Monitoring** and **Operational Resilience**.

### 5.1 Outcome Monitoring (Price & Value)
The FCA's "Consumer Duty" requires firms to prevent "sludging" (nudging users toward higher commissions or complex, unsuitable products).
*   **Implementation Pattern**: Passive Surveillance. Use a background **Forensic Agent** to sample 10% of `agent_audit` transcripts.
*   **Metric**: Detect sentiment-manipulation or "FOMO hooks" in the AI's response using an LLM-as-a-Judge.

### 5.2 Operational Resilience (Kill-Switches)
*   **Pattern**: Circuit Breakers. If the `Sentinel` identifies a sudden spike in rejected trades (velocity check), the system must have a "Kill-Switch" that puts the ecosystem into a **Text-Only Research Mode**, disabling all transactional executions automatically.

---

## 🏛️ 6. FINRA (US) Compliance: Supervision & Recordkeeping

FINRA (and the SEC) prioritizes the integrity of books and records and the supervision of all customer communications.

### 6.1 Immutable Archiving (SEC 17a-4)
All `AgentAudit` records must be stored on **WORM (Write Once Read Many)** media.
*   **Solution Architect Pattern**: Push audit logs to **Google Cloud Storage** with **Retention Policy Locks** enabled. This prevents even a super-admin from deleting a record before its legal expiry.

### 6.2 Human-in-the-Loop (HITL) for High-Stakes
*   **Threshold Pattern**: If a simulation (Actuarial) or recommendation exceeds a certain value (e.g., $50,000), the `generate_ai_response` flag must require a **Human Approval Token** before the result is displayed to the user.

---

## 🏛️ 7. GDPR (EU/UK): Privacy-by-Design & Article 22

GDPR is about **Data Minimization** and the **Right to Explanation**.

### 7.1 Automated Decision-Making (Article 22)
Under Article 22, users have the right *not* to be subject to a decision based solely on automated processing if it has legal/significant effects.
*   **Pattern: Transparency Logs**. The `Historian` must store the LLM's `THOUGHT` steps in a format that can be exported for a "Right to Explanation" request. 
*   **Opt-out**: Provide a toggle in the UI to disable "AI Recommendations," reverting to standard human-led workflows.

### 7.2 Right to Erasure (Vector DBs)
*   **Pattern: Chunk-Metadata Masking**. When a user exercises their "Right to be Forgotten," the architect must execute a `metadata.delete_by_user_id(user_pk)` across **pgvector** or **Vertex AI Search** indices to ensure vector embeddings are purged.

---

## 🏛️ 8. MiFID II: Suitability & Algorithmic Trading

MiFID II requires rigorous assessment of suitability and transparency in algorithmic interactions.

### 8.1 The Suitability Gating Logic
Every transactional intent must be checked against the user's **Internal Profile**:
1.  **Knowledge & Experience**: Can this user trade high-leverage options?
2.  **Financial Situation**: Does the user have sufficient cash buffers (The Sentinel's `MinBalanceRule`)?
3.  **Investment Objectives**: Does this asset match the target retirement age?

### 8.2 Algorithmic Trading Controls
*   **Pattern: Pre-Trade Risk Limits (PTRL)**. Implement hard exposure limits per-trade and per-day in the `Sentinel`. The AI can *propose* a trade, but the deterministic Python code in `sentinel_service.py` enforces the volume.

---

> [!IMPORTANT]
> **Summary for Architects**: Compliance is not a wrapper; it is an **Internal Gatekeeper**. By placing the `Guardian`, `Shield`, and `Sentinel` *inside* the execution loop, you ensure that the AI—regardless of its creativity—never steps outside the regulatory boundary.
