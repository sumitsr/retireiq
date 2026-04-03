RetireIQ implements a multi-layered security architecture to ensure that sensitive financial data is never leaked — neither to version control nor to external AI providers.

> [!IMPORTANT]
> For a comprehensive analysis of regulatory alignment (GDPR, MiFID II) and our layered defense-in-depth strategy, please refer to the **[Security and Compliance Blueprint](file:///Users/sumitsrivastava/.gemini/antigravity/scratch/retireiq/docs/security_and_compliance_blueprint.md)**.

---

## 1. PII Proxy: The Guardian Agent

The most critical security boundary is between user data and external LLM providers. RetireIQ uses a **symmetric anonymization proxy** pattern.

### How it Works

```
User Message/Profile  →  [Anonymize]  →  LLM (only sees tokens)  →  [De-anonymize]  →  User
"John Smith owes..."       "<PERSON_0> owes..."                      "John Smith owes..."
```

**Implementation**: `app/utils/pii_sanitizer.py` using **Microsoft Presidio**.

### Entities Redacted
| Entity Type | Example Input | Token |
|------------|--------------|-------|
| `PERSON` | "John Smith" | `<PERSON_0>` |
| `EMAIL_ADDRESS` | "john@email.com" | `<EMAIL_ADDRESS_0>` |
| `PHONE_NUMBER` | "0712345678" | `<PHONE_NUMBER_0>` |
| `SSN` | "123-45-6789" | `<SSN_0>` |
| `ACCOUNT_NUMBER` | "GB29NWBK..." | `<ACCOUNT_NUMBER_0>` |
| `LOCATION` | "London" | `<LOCATION_0>` |

### The Ghost Map (Re-hydration)
A per-request `mapping` dictionary is maintained by the `PIISanitizer` instance:
- `clear_mapping()` is called at the start of every request to prevent cross-session leakage.
- The mapping is used by `deanonymize_response()` to restore original values in the LLM's output.

> [!CAUTION]
> The Ghost Map is **in-memory only**. It is never persisted to the database or logs. This is a deliberate security constraint — the AI never "knows" it processed real PII.

---

## 2. Environment Variable Injection Strategy

All sensitive configuration (API Keys, Database Passwords, JWT Secrets) is injected at runtime using environment variables. **Nothing sensitive lives in the codebase.**

### How it Works
- **Source**: Your private `.env` file (stored locally in the project root, never committed).
- **Orchestration**: `docker-compose.yml` uses `${VARIABLE}` interpolation to pass values from the host OS into containers.
- **Application**: The Flask `Config` class fetches these values via `os.environ`.

### Fail-Fast Mechanism
The application is configured to **refuse to start** if mandatory security keys are missing:

```python
# config.py
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is not set!")
```

This prevents a misconfigured app from serving traffic with no authentication.

---

## 3. Strict Source Protection

The repository is configured with a strict `.gitignore` policy:
- `.env` and all `.env.*` files are excluded.
- Only `.env.example` is committed, providing a template without actual values.

---

## 4. Agent Audit Trail (The Historian)

For financial compliance, every AI decision is recorded in the `agent_audit` table:
- `session_id`: Ties all steps to a specific user conversation.
- `agent_name` + `step_type`: Creates a structured, queryable paper trail.
- **Zero LLM output is stored verbatim without context** — the audit record shows *why* and *how* a response was generated.

> [!NOTE]
> This audit trail is the foundation for GDPR Right-to-Explanation compliance. A customer can request a full record of what the AI knew when it made a recommendation.

---

## 5. Pre-Trade Compliance: The Sentinel Agent

For any state-changing financial operation (`TRANSACTIONAL`), RetireIQ introduces a **Deterministic Compliance Gate**.

### The Rule Chain
Before a trade reaches the Executor, the Sentinel evaluates a sequence of hard-coded rules in `app/services/sentinel_service.py`:
- **Concentration**: Prevents any single holding from exceeding 10% of the portfolio.
- **Suitability**: Ensures the asset risk class (High/Med/Low) matches the user's Risk Tolerance.
- **Min Balance**: WARNs the user if a trade would drain their cash buffer below £1,000.
- **Age Restriction**: Blocks pension drawdowns if the user is under 55 (UK regulation).

### Security Rationale
- **Not Probabilistic**: Unlike the LLM, the Sentinel uses Python logic. It cannot be "convinced" to break a rule via prompt injection.
- **Fail-Safe**: If any rule returns `BLOCK`, the transaction is aborted immediately before the external Agent API is even called.

---

## 6. Session Integrity & Memory
- **Isolation**: Each chat session has a unique `conversation_id`. Threads and SSE streams are locked to this ID.
- **Selective Memory**: Only pertinent financial facts (extracted by the `MemoryService`) are persisted. PII is scrubbed from the transcript *before* it is summarized into memories.

---

## 7. Best Practices for Contributors

- **Never hardcode strings**: Avoid using strings as fallbacks in `os.environ.get()`. If it's a secret, it should be mandatory.
- **Rotate Secrets Regularly**: In production environments, secrets should be rotated every 90 days.
- **Use Secret Management Tools**: For production deployments, use **Google Cloud Secret Manager** or **HashiCorp Vault**.
- **Model Provider Security**: When using `vertex_ai`, ensure service account credentials are injected via `GOOGLE_APPLICATION_CREDENTIALS`, never hardcoded.

---

> [!CAUTION]
> **Data Leaks**: If you accidentally commit a secret to git, you MUST consider it compromised. Rotate the secret immediately and use a tool like `git-filter-repo` to scrub the history.
