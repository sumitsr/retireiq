# AI Engineering Masterclass: Zero to Expert (The RetireIQ Case Study)

Welcome to the **RetireIQ AI Engineering Masterclass**. This document is a **zero to expert** curriculum built on the real-world, "Bank-Grade" architecture of RetireIQ as a living laboratory. Every concept, formula, and decision here maps directly to live code you can open, read, and run.

> [!NOTE]
> **How to read this document**: Each module teaches a universal AI Engineering concept first, then explains exactly *why* we made the specific implementation decisions we did in RetireIQ. The goal is that after reading this, you can build any production-grade AI system — not just this one.

---

## 🏛️ Module 1: The AI Foundations (The Vector Transformation)

### 1.1 Beyond the Autocomplete: The Transformer Architecture
While many see LLMs as simple word predictors, an Expert AI Engineer understands the **Transformer Architecture**. At its core, the "Secret Sauce" is **Multi-Head Attention**.

The seminal 2017 paper "Attention Is All You Need" (Vaswani et al.) introduced the mechanism that replaced recurrent networks (RNNs) and enabled parallel training at a massive scale.

**The Key Equations:**
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

Where:
- **$Q$ (Query)**: What the current token is looking for.
- **$K$ (Key)**: What other tokens in the sequence offer.
- **$V$ (Value)**: The actual content to aggregate if attention is high.
- **$d_k$**: The key dimension — we divide by $\sqrt{d_k}$ to prevent vanishing gradients in deep models.

> [!NOTE]
> **RetireIQ Insight: Why Three Roles?**
> In `llm_service.py`, we structure every prompt into three distinct roles — **System**, **User**, **Assistant** — because these map directly to the Transformer's contextual attention layers. The `System` role is processed with highest attention weight, establishing the "persona" that guides all downstream token predictions.

### 1.2 The Token Lifecycle & Context Windows
LLMs digest **Tokens**, not words. We use **Byte-Pair Encoding (BPE)** to split text into sub-word units.

- "Retirement" → `["Retire", "ment"]` = 2 tokens
- "RetireIQ" → `["Retire", "IQ"]` = 2 tokens

**RetireIQ Context Management**: We cap conversation history at 20 messages in `chat.py` to prevent pushing past the model's context limit (128k for GPT-4o, 1M+ for Gemini 1.5 Pro). Beyond the limit, the model literally "forgets" the beginning of the conversation.

### 1.3 Sampling Parameters: Shaping the Probability Distribution

When the LLM predicts the next token, it produces **Logits** (raw scores over the entire vocabulary — often 50,000+ tokens). **Sampling** controls how we select from this distribution.

| Parameter | Mathematical Impact | RetireIQ Usage (The Why) |
| :--- | :--- | :--- |
| **Temperature ($T$)** | Divides all logits before Softmax: $score_i / T$ | See Decision Matrix below |
| **Top-P (Nucleus)** | Dynamic threshold. Sum tokens by probability until cumulative mass $\geq P$ | Preferred for RetireIQ — adapts to the model's confidence |
| **Top-K** | Limits the pool to the $K$ most likely tokens only | Used when Top-P pools become too wide |

#### 🌡️ Deep Dive: The Temperature Decision Matrix

In RetireIQ, we don't just "pick a number." We align $T$ with the **Cognitive Load** of the task:

- **$T=0.0$ — The "Robot" (Data Extraction)**
    - *When*: `orchestrator.py` intent classification — "Is this a BUY, SELL, or INFO request?"
    - *Why*: We need **100% precision**. At $T=0$, the Softmax distribution collapses to a near-spike — the AI always picks the highest-probability token. There is no creativity, and we want none.

- **$T=0.3$ — The "Analyst" (Structured Summarization)**
    - *When*: Summarizing a 50-page investment policy document into bullet points.
    - *Why*: We want the summary to sound professional (not robotic), but we cannot risk the AI "inventing" new financial terms. A low but non-zero $T$ adds subtle linguistic variety without losing factual grounding.

- **$T=0.7$ — The "Advisor" (RetireIQ Standard Chat)**
    - *When*: General dialogue between a user and their RetireIQ advisor.
    - *Why*: **The Human Factor**. At $T=0.7$, the model uses natural sentence structures and varied vocabulary, making RetireIQ feel like a trusted human advisor. This is the balance point between creativity and accuracy — known in the industry as the "Safe Sampling Zone."

- **$T=1.0+$ — The "Poet" (Creative Tasks)**
    - *When*: "Generate 10 unique marketing names for a new retirement fund."
    - *Why*: We want the model to explore the "Long Tail" of its vocabulary. High temperature flattens the probability distribution, allowing surprising, novel tokens to emerge.

> [!IMPORTANT]
> **Expert Warning: The Hallucination Gradient**
> As $T$ increases from 0 → 1, hallucination risk increases non-linearly. In "Bank-Grade" systems like RetireIQ, we hard-cap at $T=0.7$ for all user-facing responses. Financial advice that sounds creative but is factually wrong is far more dangerous than advice that sounds repetitive but is correct.

---

## 🧠 Module 2: The Vector Mind (Geometry vs. Keywords)

### 2.1 The Problem: Semantic vs. Lexical Search
A standard database `LIKE '%retirement%'` query fails if your document uses "pension savings" instead. **This is the core problem RAG solves**.

A user asking *"How much can I put into my pension this year?"* must match against a document containing *"Annual 401k contribution limits for pre-retirees..."* — zero shared keywords, identical semantic intent.

### 2.2 Embeddings & High-Dimensional Geometry
We pass text through an **Encoder model** (e.g., `all-minilm`, `text-embedding-004`) and receive a vector of ~384–3072 floating point numbers.

**The Geometric Insight**: Similar meanings cluster in high-dimensional space. The vector for "pension" is geometrically close (small cosine distance) to "401k" even though the two words share no characters.

$$\text{Cosine Similarity} = \frac{A \cdot B}{||A|| \cdot ||B||}$$

This is how `knowledge_service.py` finds relevant policy snippets — it computes this distance across every stored vector.

### 2.3 The Full RAG Pipeline

```
1. INGESTION TIME:
   PDF/Policy Text
       ↓  Chunk (512 tokens)
   ["Fixed income fund risks...", "401k contribution limits..."]
       ↓  Embed (text-embedding-004 or all-minilm)
   [[0.23, -0.41, 0.78, ...], [0.11, 0.09, -0.55, ...]]
       ↓  Store
   pgvector / Vertex AI Vector Search

2. QUERY TIME:
   User Question → Embed → Query Vector
       ↓  Cosine Distance Search (HNSW)
   Top-K nearest chunks
       ↓  Inject into prompt
   Grounded, factual LLM response
```

### 2.4 Search Engineering: HNSW Indexing
Searching linearly through 1 million vectors is $O(n)$ — too slow for a real-time chatbot. **HNSW (Hierarchical Navigable Small Worlds)** reduces this to approximately $O(\log n)$ by building a multi-layer graph where each node connects to its nearest neighbors.

**Live Implementation**: [knowledge_service.py](../app/services/knowledge_service.py) — `query_knowledge()` uses pgvector's `cosine_distance` operator, backed by an HNSW index in PostgreSQL.

> [!TIP]
> **RetireIQ Rationale: Why pgvector and not a dedicated vector DB?**
> We keep vectors in the same PostgreSQL instance as our users and conversations. This allows us to do **filtered similarity search** ("find the most similar policy snippet *for this specific product tier*") using SQL `WHERE` clauses alongside vector distance — something standalone vector DBs make complex.

---

## 🧠 Module 3: The Retrieval Paradox (RAG vs. Long-Context)

With the rise of "Infinite Context" models (Gemini 1.5 Pro supports 2M tokens), many ask: **Is RAG dead?** In a "Bank-Grade" system, the answer is a resounding **No**. This module explains why retrieval remains the dominant cost and performance lever.

### 3.1 The "Token Tax" (Latency and Cost at Scale)

Processing 500,000 tokens on every user message:
- **Latency**: Even at 2ms/1k tokens, that's 1 full second just on input processing.
- **Cost**: Gemini 1.5 Pro charges ~$3.50 per 1M input tokens. 10,000 users × 500k tokens = **$17,500/day**.

RAG retrieves only the top-5 relevant chunks (~2,500 tokens): **Cost: ~$0.009 per query**.

### 3.2 The "Lost in the Middle" Phenomenon
Stanford NLP research (Liu et al., 2023) showed LLM performance **degrades significantly** when the relevant answer is in the *middle* of a long context. Models reliably find information at the very beginning and end but "drift" or ignore content buried in the middle of 500k+ tokens.

**RAG as a Spotlight**: By providing only 5–10 curated, highly relevant snippets, we ensure the model's full attention mechanism is focused precisely on the facts that matter.

### 3.3 The Expert Strategy Matrix

| Feature | Long-Context Only | RAG-First (The RetireIQ Way) | Hybrid (Best of Both) |
| :--- | :--- | :--- | :--- |
| **Cost** | 💸 Exponential | 💰 Predictable | 💰 Optimized |
| **Speed** | 🐢 High latency | ⚡ Fast | ⚡ Fast + Smart Cache |
| **Accuracy** | 📉 Drifts in the middle | 🎯 High precision | 🎯 Highest precision |
| **Privacy** | 🔓 Context bleed risk | 🔒 DB-level boundaries | 🔒 Isolated |
| **Freshness** | 📅 Model cutoff only | ✅ Real-time via DB | ✅ Real-time |

> [!NOTE]
> **RetireIQ Hybrid Pattern**: We use RAG for standard knowledge queries and **Vertex AI Context Caching** (Module 12) for large, stable policy documents that are accessed many times per hour. This gives us RAG's precision with context caching's near-zero repeated token cost.

---

## 🏗️ Module 4: Multi-Agent Systems (The Collaborative Brain)

Moving beyond a "Single-Bot" architecture is the key to building specialized financial intelligence.

### 4.1 Why Single-Agent Fails at Scale

A single agent given a massive system prompt faces:
1. **Instruction Dilution**: A 10,000-token system prompt reduces effective attention on any single instruction.
2. **Tool Confusion**: An agent with 50 tools available has high probability of calling the wrong one.
3. **Context Pollution**: A trading instruction in one part of the conversation affects a retirement planning answer later.

### 4.2 The ReAct Pattern (Reason + Act)

The standard agentic reasoning loop:

```
THOUGHT: "The user wants to know their portfolio balance."
ACTION: call_tool("get_portfolio", {"user_id": "u123"})
OBSERVATION: {"cash": 12000, "equity": 45000, "bonds": 20000}
THOUGHT: "I have the data. I'll format a friendly summary."
RESPONSE: "Your current portfolio is valued at $77,000 across..."
```

RetireIQ's **Historian** (`audit_service.py`) records every single step in this loop into the `agent_audit` table.

### 4.3 The Orchestrator / Dispatcher Pattern

Rather than one agent trying to handle all domains, we use a **Semantic Router** that operates as the "Air Traffic Controller":

```
User Message → [Dispatcher: Gemini Flash, T=0.0]
                      ↓ JSON classification
               {intent: "KNOWLEDGE_BASE", confidence: 0.97}
                      ↓
               [Scholar Agent: Gemini Pro + RAG]
                      ↓
               Grounded policy answer
```

**Instruction Blast Isolation**: The Scholar Agent's system prompt only includes *knowledge retrieval* instructions. It has no awareness of trading tools. This reduces hallucination probability and attack surface simultaneously.

**Live Implementation**: [orchestrator.py](../app/services/orchestrator.py) — The `dispatch()` method routes to `_handle_knowledge_query()`, `call_agent_api()`, or returns `None` (falls back to general LLM).

### 4.4 Intent Domain Taxonomy

| Intent | Agent | Key Signal Words |
|--------|-------|-----------------|
| `KNOWLEDGE_BASE` | Scholar (RAG) | "What is", "explain", "how does", "policy" |
| `PORTFOLIO_ANALYSIS` | Analyst | "balance", "performance", "projection", "goal" |
| `TRANSACTIONAL` | Executor | "buy", "sell", "transfer", "register", "change" |
| `GENERAL` | General LLM | "hello", "thanks", "what can you do" |

### 4.5 Advanced: Tool-Use (Function Calling)

When an LLM "calls a tool," it generates a structured JSON output matching a schema we defined:

```json
{
  "tool": "get_account_balance",
  "arguments": { "user_id": "u123", "account_type": "equity" }
}
```

The agent runtime intercepts this, executes the function, and feeds the result back as an **OBSERVATION**. This is the foundation of all agentic behavior.

---

## 🛡️ Module 5: Mission-Critical Security (The PII Proxy — The Guardian Agent)

In a financial system, sending raw user data to an external LLM (OpenAI, Gemini, etc.) is a regulatory and trust violation. The "Bank Data Paradox" is: *"The AI needs context to give good advice, but it must never see real PII."*

### 5.1 The De-identification Lifecycle (The "Ghost Map" Pattern)

We solve this with a symmetric transformation proxy:

```
STEP 1: ANONYMIZE (Entry Firewall)
─────────────────────────────────
Raw:   "Hi, I'm John Smith (SSN: 123-45-6789). What are my options?"
Ghost: "Hi, I'm <PERSON_0> (SSN: <SSN_0>). What are my options?"
Map:   { "<PERSON_0>": "John Smith", "<SSN_0>": "123-45-6789" }

STEP 2: LLM PREDICTION (External Call)
────────────────────────────────────────
LLM sees ONLY: "Hi, I'm <PERSON_0> (SSN: <SSN_0>). What are my options?"
LLM responds:  "Hello <PERSON_0>! Based on your profile, I recommend..."

STEP 3: RE-HYDRATION (Exit Reconstruction)
──────────────────────────────────────────
Response: "Hello <PERSON_0>! Based on your profile, I recommend..."
Output:   "Hello John Smith! Based on your profile, I recommend..."
```

The `mapping` dictionary (the "Ghost Map") never leaves the RetireIQ server. It lives only in memory for the duration of a single request.

### 5.2 Entity Recognition: The Two-Layer Approach

**Layer 1 — Statistical NER (Presidio/spaCy)**: Detects `PERSON`, `LOCATION`, `EMAIL_ADDRESS`, `PHONE_NUMBER` using ML models trained on millions of annotated examples.

**Layer 2 — Domain-Specific Regex**: Catches financial entities that general NER models miss:
```python
# Custom SSN Pattern (Bank-Grade)
ssn_pattern = Pattern(name="ssn_pattern", regex=r"\b\d{3}-\d{2}-\d{4}\b", score=0.5)

# Account Number Pattern (AU/UK/US bank format)
account_pattern = Pattern(name="account_pattern", regex=r"\b[A-Z]{2,4}\d{5,12}\b", score=0.6)
```

### 5.3 Security Properties

1. **Session Isolation**: `sanitizer.clear_mapping()` is called at the start of *every* request. There is zero cross-session ghost map contamination.
2. **Sort-by-length De-anonymization**: We sort placeholders by string length (descending) before re-hydration to prevent `<PERSON_10>` being partially matched by `<PERSON_1>`.
3. **Local-First Option**: When `LLM_PROVIDER=ollama`, all data stays on-premise. The PII proxy becomes a belt-and-suspenders defensive measure.

**Live Implementation**: [pii_sanitizer.py](../app/utils/pii_sanitizer.py)

---

## ⚖️ Module 6: Evaluation (The Hallucination Firewall)

### 6.1 Why AI Testing is Different from Software Testing

Traditional software is **deterministic**: given the same input, `add(2, 3)` always returns `5`.

An LLM is **probabilistic**: given "What's the stock market outlook?", it returns a different answer every single time — and sometimes invents facts.

This is why RetireIQ treats **>90% code coverage** as a non-negotiable hard floor.

### 6.2 The RAGAS Framework (RAG Assessment Score)

For evaluating our retrieval quality, we use the **RAGAS** metric suite:

| Metric | What it Measures | Target |
|--------|-----------------|--------|
| **Faithfulness** | Is the response grounded in the retrieved context? | > 0.85 |
| **Answer Relevancy** | Does the answer actually address the question? | > 0.80 |
| **Context Recall** | Did retrieval find all the necessary information? | > 0.75 |
| **Context Precision** | Was the retrieved context actually relevant? | > 0.80 |

### 6.3 The RetireIQ Testing Philosophy: Mock-First

We use `unittest.mock.patch` to isolate every external dependency, enabling deterministic assertions:

```python
# Pattern: Mock the LLM, test the business logic
@patch("app.services.llm_service.dispatcher.dispatch", return_value=None)
@patch("app.services.llm_service.call_azure_openai_api_with_key")
def test_generate_ai_response(mock_azure, mock_dispatch):
    mock_azure.return_value = "Safe investment advice"
    result = generate_ai_response("What should I invest in?")
    assert result == "Safe investment advice"
    mock_dispatch.assert_called_once()  # Verify dispatch was invoked
```

**Why this works**: We control the LLM's "answer," so our assertions test the *orchestration logic* — not the model's creativity. The model's quality is tested separately (via RAGAS on a held-out dataset), keeping concerns cleanly separated.

### 6.4 Test Taxonomy (The 3-Layer Pyramid)

```
         [E2E / Integration Tests]
              - test_routes.py
              - Full request lifecycle
         ─────────────────────────────
        [Service Unit Tests]
         - test_orchestrator.py
         - test_llm_service.py
         - test_sse_service.py
         ─────────────────────────────────────
    [Model / Utility Tests]
     - test_memory_service.py
     - test_vertex_service.py
     - Pure function, no network calls
```

> [!IMPORTANT]
> **The Golden Rule of AI Engineering**
> "If you can't test it, don't deploy it." RetireIQ's stability is built on 74 passing tests, not just the model's intelligence. New features **must** include tests for both the success path and every error path.

---

## 🚀 Module 7: Scaling LLM Platforms (GCP, Azure, Ollama)

### 7.1 The Provider Abstraction Principle

A production AI system should be **provider-agnostic**. A business decision (switch from Azure to GCP) should not require rewriting application code. In RetireIQ, we achieve this with an environment variable strategy:

```
LLM_PROVIDER=vertex_ai  →  call_vertex_ai_api()
LLM_PROVIDER=azure_openai  →  call_azure_openai_api_with_key()
LLM_PROVIDER=openai  →  call_openai_api()
LLM_PROVIDER=ollama  →  call_ollama_api()
```

All paths produce the same output: a string. The rest of the application never knows which provider was used.

### 7.2 Azure OpenAI vs. OpenAI Direct

| Feature | OpenAI Direct | Azure OpenAI |
|---------|--------------|-------------|
| **Data Residency** | US by default | Your chosen Azure region |
| **Compliance** | SOC 2 | SOC 2, ISO 27001, HIPAA, **PCI DSS** |
| **Network Security** | Public internet | Private VNet integration |
| **Pricing** | Pay-per-token | Pay-per-token + Enterprise discounts |

**RetireIQ Default = `azure_openai`** because financial data requires PCI DSS compliance, which is only available on Azure's hosted OpenAI deployments.

### 7.3 Ollama: Zero-Cost Local LLMs

Ollama runs open-source models (Llama3, Mistral, Phi-3) locally, making it ideal for:
- **Development**: No cloud bill while coding.
- **Privacy Testing**: Verify the PII proxy works without any external call.
- **Offline Environments**: Air-gapped financial institutions.

```bash
# Pull the two models RetireIQ needs
ollama pull llama3       # Chat / Reasoning
ollama pull all-minilm   # Embeddings (for RAG)
```

---

## 🧪 Module 8: AI Testing Patterns (The Reliability Barrier)

### 8.1 `patch.multiple()` — The MAS Testing Pattern

When a service depends on multiple mocked components simultaneously, nested `with patch()` blocks become unreadable. The expert pattern is `patch.multiple()`:

```python
# Testing Vertex AI when SDK is not installed (GenerativeModel = None)
with patch.multiple(
    'app.services.llm_service',
    vertexai=MagicMock(),            # Make SDK "available"
    GenerativeModel=mock_model_class, # Replace None with our mock
    GenerationConfig=MagicMock(),    # Replace None config class
):
    response = call_vertex_ai_api("Hello", "gemini-1.5-pro")
    assert response == "GCP Response"
```

**The Why**: The Vertex AI SDK isn't installed in local dev. SDK classes default to `None`. Standard `patch()` replaces `None` with a Mock, but the function still calls `None(...)` (not the mock) if imported at module load time. `patch.multiple` patches the entire module namespace atomically.

### 8.2 Testing MAS Architecture: The Cascade Problem

In a multi-agent system, a bug in a lower-level service (e.g., `audit_service`) can fail tests for a higher-level service (`orchestrator`). The solution is **explicit layer mocking**:

```python
# Test ONLY the orchestrator's routing logic
# Mock the audit service so DB errors don't cascade into orchestrator tests
with patch.object(dispatcher, '_classify_intent', return_value=mock_intent):
    with patch.object(dispatcher, '_handle_knowledge_query', return_value="result"):
        response = dispatcher.dispatch("What is a 401k?", {}, [], "session-1")
```

---

## 🧠 Module 9: Multi-Agent Orchestration in Depth (The Dispatcher Pattern)

### 9.1 The Full Dispatch Lifecycle

```python
# orchestrator.py — The full flow
def dispatch(self, sanitized_message, user_profile, history, conversation_id):
    # 1. Log to Historian (THOUGHT)
    historian.log_step(session_id=conversation_id, agent_name="Dispatcher",
                       step_type="THOUGHT", content="Resolving intent...")

    # 2. Fast classification (Gemini Flash, T=0.0)
    intent_data = self._classify_intent(sanitized_message, user_profile, history)

    # 3. Log classification result (ACTION)
    historian.log_step(session_id=conversation_id, agent_name="Dispatcher",
                       step_type="ACTION", content=f"Intent: {intent_data['intent']}")

    # 4. Route to specialist
    if intent_data['intent'] == 'KNOWLEDGE_BASE':
        return self._handle_knowledge_query(sanitized_message, conversation_id)
    elif intent_data['intent'] in ['TRANSACTIONAL', 'PORTFOLIO_ANALYSIS']:
        return call_agent_api(intent_data, user_profile.get("id"))
    return None  # Fall through to general LLM
```

### 9.2 Classification Prompt Engineering

The Dispatcher's classification prompt is deliberately **constrained**:

```
You are the RetireIQ Dispatcher Agent. Your ONLY job is to classify the user's intent
into exactly one of these categories:
1. KNOWLEDGE_BASE: Questions about retirement policies...
2. PORTFOLIO_ANALYSIS: Requests for account balances...
3. TRANSACTIONAL: Requests to buy/sell assets...
4. GENERAL: Greetings, thanks, or unrelated chit-chat.

Output ONLY a JSON object:
{ "intent": "CATEGORY", "sub_intent": "brief description", "confidence": 0.0-1.0 }
```

**Why `T=0.0` here?**: We need deterministic JSON output. At `T=0.0`, the model will always produce the same classification for the same message — making the system testable and predictable.

### 9.3 Confidence Thresholds (Future Enhancement)

A production-grade version adds confidence routing:
- `confidence > 0.85`: Route as classified.
- `0.60 < confidence < 0.85`: Route but flag for human review.
- `confidence < 0.60`: Ask the user for clarification before routing.

---

## 🏛️ Module 10: The Historian Pattern (Audit Trails & Compliance)

### 10.1 Why Standard Logging Fails for AI

Standard logging captures *what happened*. The Historian captures *why the AI decided what it decided*. This distinction is critical for:
- **Financial Compliance**: "Show me every reason this portfolio recommendation was made."
- **Model Debugging**: "Why did the agent classify that as TRANSACTIONAL instead of KNOWLEDGE_BASE?"
- **GDPR Right-to-Explanation**: A customer's right to understand automated decisions.

### 10.2 The AgentAudit Schema

```python
class AgentAudit(db.Model):
    session_id   = db.Column(db.String(36), index=True)  # Links all steps for one request
    agent_name   = db.Column(db.String(50))              # "Dispatcher", "Scholar", "Guardian"
    step_type    = db.Column(db.String(20))              # "THOUGHT", "ACTION", "OBSERVATION", "RESPONSE"
    content      = db.Column(db.Text)                    # The raw reasoning text
    step_metadata= db.Column(JSON)                       # {"model": "gemini-flash", "latency_ms": 240}
    created_at   = db.Column(db.DateTime)
```

**A complete audit trail for one request looks like:**

```
session_id: "conv-123"
─────────────────────────────────────────────────────
[Guardian]  THOUGHT     "Initializing PII sanitization..."
[Guardian]  ACTION      "Anonymization complete. 2 entities masked."
[Dispatcher] THOUGHT    "Resolving intent: 'What is a Roth IRA?'"
[Dispatcher] ACTION     "Intent resolved: KNOWLEDGE_BASE (conf: 0.97)"
[Scholar]    THOUGHT     "Searching knowledge base for: Roth IRA"
[Scholar]    OBSERVATION "Found 3 relevant policy snippets."
[Guardian]  RESPONSE    "Response de-anonymized and delivered."
```

### 10.3 Audit + SSE Integration

The Historian's `log_step` simultaneously writes to DB **and** broadcasts to the SSE stream:

```python
# audit_service.py
db.session.commit()
sse_service.publish(session_id=session_id, event="agent_step",
                    data={"agent": agent_name, "type": step_type, "content": str(content)})
```

This single function call achieves two goals:
1. **Persistence**: Immutable compliance record in the database.  
2. **Transparency**: Real-time Chain-of-Thought stream for the user interface.

---

## ⚡ Module 11: Real-time UX & Agentic Transparency (SSE)

### 11.1 WebSockets vs. SSE vs. Polling

| Mechanism | Direction | Complexity | Best For |
|-----------|-----------|-----------|---------|
| **Short Polling** | Client → Server (repeated) | Low | Simple status checks |
| **Long Polling** | Server holds response | Medium | Near-real-time updates |
| **WebSockets** | Bidirectional | High | Chat, games, collaborative apps |
| **SSE (us)** | Server → Client (one-way) | **Low** | **Streaming AI reasoning steps** |

**Why SSE for RetireIQ**: The agent's reasoning is inherently one-directional — the server pushes updates; the client only observes. SSE is the lowest-complexity mechanism that achieves this perfectly.

### 11.2 The SSE Wire Protocol

SSE events are newline-delimited plain text:

```
event: agent_step
data: {"agent": "Dispatcher", "type": "THOUGHT", "content": "Resolving intent..."}

event: agent_step
data: {"agent": "Scholar", "type": "OBSERVATION", "content": "Found 3 snippets."}

event: final_response
data: {"content": "Based on our policies, a Roth IRA...", "message_id": 42}

event: ping
data: {"time": 1712088000.0}
```

The trailing double newline (`\n\n`) is the SSE **event boundary**. The client's `EventSource` API handles parsing automatically.

### 11.3 The Thread-Safe Queue Architecture

The SSE service uses Python's `queue.Queue` to bridge the background agent thread and the streaming response:

```
[Background Thread: Agent Worker]
        ↓ q.put(event)
   [queue.Queue]  ← Thread boundary (thread-safe)
        ↓ q.get(timeout=20)
[Flask Response Generator: SSE subscriber]
        ↓ yield "event: ...\ndata: ...\n\n"
  [Client EventSource]
```

**The Heartbeat**: If the queue is empty for 20 seconds, a `ping` event is yielded to prevent proxy/load-balancer connection timeouts. This is critical in production where Nginx/Cloud Run have default 30-second idle connection timeouts.

**Live Implementation**: [sse_service.py](../app/services/sse_service.py)

---

## ☁️ Module 12: Enterprise Scaling & Vertex AI (Context Caching)

### 12.1 Model Tiering: The Cost-Performance Matrix

Not every task requires a frontier model. We implement **Tiered Model Selection**:

| Task | Model | Why |
|------|-------|-----|
| Intent Classification (Dispatcher) | Gemini 1.5 **Flash** | Sub-100ms, ~50x cheaper than Pro |
| Policy Grounded Q&A (Scholar) | Gemini 1.5 **Pro** | Superior multi-document reasoning |
| Semantic Embeddings (RAG) | text-embedding-004 | Purpose-built, lowest cost per token |
| General Chat (Fallback) | Gemini 1.5 **Pro** | Full reasoning capability |

**RetireIQ Default Logic** (`llm_service.py`):
```python
provider = os.getenv("LLM_PROVIDER", "azure_openai")
default_model = "gemini-1.5-pro" if provider == "vertex_ai" else "gpt-4o"
model = os.getenv("LLM_MODEL_NAME") or default_model
```

### 12.2 Vertex AI Context Caching: The 90% Token Reduction

For a financial institution with 10,000+ pages of policy documents, sending the full corpus with every request is cost-prohibitive.

**The Math:**
- Without caching: `50,000 tokens × $3.50/1M = $0.175 per query`
- With caching: `50 tokens + cache storage = ~$0.007 per query`
- **Saving: 96%**

**The Implementation:**
```python
# VertexCacheManager (knowledge_service.py)
cache = caching.CachedContent.create(
    model_name="gemini-1.5-pro",
    contents=[large_policy_text],
    system_instruction="You are a RetireIQ policy expert...",
    ttl=3600,  # 1 hour TTL
)
# Cache ID returned: "projects/.../cachedContents/abc123"
# All subsequent requests reference this ID — only the user question is sent
```

### 12.3 Cache TTL Strategy: The Break-Even Analysis

Caches have a storage cost even when not in use. The optimal TTL depends on query frequency:

```
Token Input Cost = $3.50 / 1M tokens
Cache Storage = $0.02 / hour / 1M tokens

Break-Even:
  If hit_rate × input_saved > storage_cost
  If 2+ queries/hour on the same document → cache is profitable
```

**RetireIQ Strategy**:
- Popular policy documents (accessed 100+/day) → `ttl=86400` (24h cache)
- Niche documents → Standard RAG (no cache)
- User-personalized context → No cache (user-specific, no sharing)

**Live Implementation**: [knowledge_service.py](../app/services/knowledge_service.py) → `VertexCacheManager`

---

## ⚖️ Module 13: Compliance Engineering (The Sentinel Pattern)

### 13.1 Why Every AI Financial System Needs a Pre-Execution Guard

An AI that can *execute* financial transactions is not just a product — it is a regulated financial service. Under FCA (UK), FINRA (US), and MiFID II (EU), every trade must pass through a suitability and compliance check before execution. The Sentinel is the implementation of this regulatory requirement as an agent.

### 13.2 The Rules Engine Architecture

A compliance rules engine is not an LLM. Regulatory rules are **deterministic** — a trade either violates a concentration limit or it doesn't. The Sentinel uses a layered decision tree:

```python
class SentinelAgent:
    """Pre-trade compliance gate — must run before any Executor call."""

    RULES = [
        ConcentrationRule(max_single_stock_pct=0.10),   # No stock > 10% of portfolio
        SuitabilityRule(),                              # Risk profile vs. asset risk class
        AMLRule(provider="ComplyAdvantage"),            # AML watchlist check
        JurisdictionRule(),                             # Age-based + geographic restrictions
    ]

    def check(self, trade_intent, user_profile):
        """Returns a ComplianceVerdict: PASS | WARN | BLOCK."""
        for rule in self.RULES:
            verdict = rule.evaluate(trade_intent, user_profile)
            if verdict.status == "BLOCK":
                historian.log_step(agent_name="Sentinel", step_type="ACTION",
                                   content=f"BLOCK: {verdict.reason}")
                return verdict  # Fail-fast: first BLOCK aborts the chain

        return ComplianceVerdict(status="PASS")
```

**The Key Property**: Rules are **auditable by non-engineers**. A compliance officer can read `ConcentrationRule(max_single_stock_pct=0.10)` and understand exactly what the system enforces — without reading LLM prompts.

### 13.3 The WARN Pattern (Human-in-the-Loop)

Not every compliance issue is a hard BLOCK. `WARN` verdicts trigger a **Human-in-the-Loop (HITL)** handoff:
```
WARN → Log to AgentAudit → SSE event: "compliance_review_required"
     → Notify compliance team (Slack/PagerDuty webhook)
     → Trade suspended pending human approval (72h timeout)
```

This pattern satisfies the MiFID II requirement for "appropriate human oversight" of automated investment decisions.

---

## 📊 Module 14: Probabilistic Planning (The Actuarial Pattern)

### 14.1 Why Deterministic Answers Fail Retirement Planning

A bank account calculator tells you: *"At 5% annual growth, £100,000 becomes £163,000 in 10 years."* This is **deterministically wrong** — markets don't return exactly 5% every year. Some years are up 20%, some are down 30%.

Retirement planning requires **probabilistic answers** that model this uncertainty honestly.

### 14.2 Monte Carlo Simulation — The Core Algorithm

```python
import numpy as np

def monte_carlo_retirement(
    initial_portfolio: float,     # Current savings: £500,000
    monthly_contribution: float,  # Monthly saving: £1,000
    annual_withdrawal: float,     # Yearly spend in retirement: £40,000
    years_to_retirement: int,     # Time horizon: 20 years
    years_in_retirement: int,     # Life expectancy after retire: 25 years
    simulations: int = 10_000,
    mean_annual_return: float = 0.07,
    annual_std_dev: float = 0.15,
) -> float:
    """Returns the probability (0–1) of not outliving your savings."""
    success = 0

    for _ in range(simulations):
        portfolio = initial_portfolio

        # Accumulation phase: saving toward retirement
        for _ in range(years_to_retirement):
            r = np.random.normal(mean_annual_return, annual_std_dev)
            portfolio = portfolio * (1 + r) + (monthly_contribution * 12)

        # Decumulation phase: spending in retirement
        for _ in range(years_in_retirement):
            r = np.random.normal(mean_annual_return - 0.01, annual_std_dev)  # Lower return assumption
            portfolio = portfolio * (1 + r) - annual_withdrawal
            if portfolio <= 0:
                break  # Portfolio exhausted — this simulation failed

        if portfolio > 0:
            success += 1

    return success / simulations  # e.g. 0.78 → "78% probability of success"
```

### 14.3 The "Sequence of Returns" Risk

One of the most counterintuitive retirement risks: *the order of returns matters more than the average return*. A severe bear market in the **first 5 years of retirement** is catastrophic — you are forced to sell depressed assets to fund living expenses. The same bear market 20 years in is manageable.

Monte Carlo models this naturally because each simulation draws random year-by-year returns — some will have the crash early, some late. The probability output captures this asymmetry.

### 14.4 Output: Confidence Bands (Plotly)

```python
# The 10th, 50th, and 90th percentile portfolio values across simulations
# form confidence bands — the "fan chart" used by central banks and pension funds

fig.add_trace(go.Scatter(x=years, y=p10_values, name="Pessimistic (10th %ile)",
                          fill=None, line=dict(color="red")))
fig.add_trace(go.Scatter(x=years, y=p50_values, name="Median (50th %ile)",
                          fill="tonexty", line=dict(color="orange")))
fig.add_trace(go.Scatter(x=years, y=p90_values, name="Optimistic (90th %ile)",
                          fill="tonexty", line=dict(color="green")))
```

---

## 🧠 Module 15: Behavioral Finance & Sentiment Engineering (The Empath Pattern)

### 15.1 Why Human Behavior is the Biggest Risk Factor

Nobel Laureate Daniel Kahneman (Thinking, Fast and Slow) identified that investors reliably:
- **Sell at the bottom** (panic selling — loss aversion: losses feel ~2× worse than equal gains)
- **Buy at the top** (FOMO — recency bias: recent returns feel permanent)
- **Hold losers too long** (status quo bias: losses are "unrealised" until you sell)

DALBAR's annual study consistently shows that **actual investor returns lag fund returns by 2–4%/year** — entirely due to behavioral timing errors. The Empath agent is RetireIQ's answer to this.

### 15.2 Real-Time Sentiment Detection

```python
PANIC_SIGNALS = [
    "sell everything", "get out now", "crash", "scared",
    "losing everything", "can't sleep", "should i panic"
]

FOMO_SIGNALS = [
    "bitcoin", "crypto", "gamestop", "all in", "missing out",
    "everyone is making money", "should i put everything in"
]

class EmpathAgent:
    def analyse(self, message: str) -> dict:
        message_lower = message.lower()

        # Rule-based bias check (fast, deterministic)
        detected_bias = "FOMO" if any(s in message_lower for s in FOMO_SIGNALS) \
                   else "PANIC" if any(s in message_lower for s in PANIC_SIGNALS) \
                   else "NONE"

        # Sentiment score (0.0 = extreme panic, 1.0 = calm confidence)
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        vs = SentimentIntensityAnalyzer().polarity_scores(message)
        compound = (vs["compound"] + 1) / 2  # normalise from [-1,1] to [0,1]

        return {
            "sentiment_score": compound,
            "detected_bias": detected_bias,
            "tone_adjustment": self._tone_for(detected_bias, compound),
        }

    def _tone_for(self, bias: str, score: float) -> str:
        if bias == "PANIC" or score < 0.3:
            return "CALMING"     # "I understand this feels alarming. Let's look at the data."
        elif bias == "FOMO":
            return "CAUTIONARY"  # "I hear the excitement. Let me share some context..."
        return "STANDARD"
```

### 15.3 Dynamic System Prompt Injection

The Empath's output modifies the LLM's `system_prompt` *before* the response is generated:

```python
# Tone variants injected into system prompt preamble
TONE_PROMPTS = {
    "CALMING": "The user appears anxious. Begin with empathy. Use grounding language. Prioritise long-term perspective. Avoid market jargon.",
    "CAUTIONARY": "The user may be experiencing FOMO. Be cautious but not dismissive. Present balanced risk/reward framing. Cite historical data.",
    "STANDARD": "Maintain your standard professional advisor tone.",
}

def inject_tone(system_prompt: str, tone: str) -> str:
    return f"{TONE_PROMPTS.get(tone, '')} {system_prompt}"
```

### 15.4 Empath → Sentinel Escalation

High-risk emotional decisions (PANIC + low score, or FOMO + large portfolio impact) are automatically flagged to the Sentinel with a `BEHAVIORAL_RISK` flag, triggering an additional "Are you sure?" confirmation step — mimicking industry-standard "best interest" duty checks.

---

*This concludes the Complete AI Engineering Series. RetireIQ is the living laboratory where every module above has a corresponding implementation you can run, modify, and experiment with. The goal was never just to build a chatbot — it was to teach the engineering principles that make AI systems trustworthy, compliant, and genuinely helpful at scale.*
