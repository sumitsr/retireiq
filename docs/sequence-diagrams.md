# Application Sequence Diagrams

The following flows show the lifecycle of typical requests in the RetireIQ Multi-Agent System.

---

## 1. Full Agentic Chat Flow (MAS with SSE Streaming)

This flow demonstrates the complete end-to-end pipeline through the Dispatcher, Historian, and SSE stream.

```mermaid
sequenceDiagram
    participant Client
    participant API as Flask API Gateway
    participant Guardian as Guardian Agent (PII)
    participant Dispatcher as Dispatcher Agent (Router)
    participant Scholar as Scholar Agent (RAG)
    participant LLM as LLM Provider (Vertex/OpenAI/Ollama)
    participant Historian as Historian (Audit DB)
    participant SSE as SSE Stream Dispatcher

    Client->>API: POST /api/chat/message {message, stream:true}
    API-->>Client: 202 Accepted {conversation_id}

    Client->>SSE: GET /api/chat/stream/<conversation_id>
    SSE-->>Client: event: connected

    Note over API: Background thread starts

    API->>Guardian: Anonymize user profile + message (Presidio)
    Guardian->>Historian: log THOUGHT "Initializing PII sanitization"
    Historian->>SSE: Broadcast agent_step (Guardian/THOUGHT)
    SSE-->>Client: event: agent_step {Guardian: Initializing PII...}
    Guardian-->>API: Sanitized message + ghost map

    API->>Dispatcher: dispatch(sanitized_message, session_id)
    Dispatcher->>Historian: log THOUGHT "Resolving intent..."
    Historian->>SSE: Broadcast agent_step (Dispatcher/THOUGHT)
    SSE-->>Client: event: agent_step {Dispatcher: Resolving intent...}

    Dispatcher->>LLM: Classify intent (Gemini Flash, T=0.0)
    LLM-->>Dispatcher: {intent: KNOWLEDGE_BASE, confidence: 0.97}
    Dispatcher->>Historian: log ACTION "Intent resolved: KNOWLEDGE_BASE"
    Historian->>SSE: Broadcast agent_step (Dispatcher/ACTION)
    SSE-->>Client: event: agent_step {Dispatcher: Intent resolved}

    Dispatcher->>Scholar: handle_knowledge_query(message)
    Scholar->>Historian: log THOUGHT "Searching knowledge base..."
    Historian->>SSE: Broadcast agent_step (Scholar/THOUGHT)
    SSE-->>Client: event: agent_step {Scholar: Searching knowledge base...}
    Scholar-->>Dispatcher: Grounded policy response

    Dispatcher-->>API: Final agent response
    Guardian->>Guardian: De-anonymize response (re-hydrate ghost map)
    Guardian->>Historian: log RESPONSE "Ready for delivery"
    Historian->>SSE: Broadcast agent_step (Guardian/RESPONSE)

    API->>SSE: Broadcast final_response {content, message_id}
    SSE-->>Client: event: final_response {content: "Based on our policies..."}
```

---

## 2. Intent Classification: Dispatcher Branch Logic

This flow shows how the Dispatcher routes different intent types.

```mermaid
graph TD
    UserMessage["User Message"] --> Guardian["Guardian: PII Anonymize"]
    Guardian --> Dispatcher["Dispatcher Agent\nGemini Flash Classification"]

    Dispatcher -->|"KNOWLEDGE_BASE\n(Policy questions, 401k rules)"| Scholar["Scholar Agent\nRAG + pgvector/Vertex Cache"]
    Dispatcher -->|"PORTFOLIO_ANALYSIS\n(Balance, projections)"| Analyst["Analyst Agent\nRecommender Engine"]
    Dispatcher -->|"TRANSACTIONAL\n(Buy/Sell, account changes)"| Executor["Executor Agent\nExternal Agent API"]
    Dispatcher -->|"GENERAL\n(Greetings, small talk)"| Fallback["General LLM\nGemini Pro / GPT-4o / Ollama"]

    Scholar --> Guardian2["Guardian: De-anonymize"]
    Analyst --> Guardian2
    Executor --> Guardian2
    Fallback --> Guardian2

    Guardian2 --> Client["Client Response + SSE Final Event"]
```

---

## 3. Context Caching Flow (Scholar Agent + Vertex AI)

This flow shows the 90% token reduction pattern for large policy documents.

```mermaid
sequenceDiagram
    participant Scholar
    participant CacheManager as VertexCacheManager
    participant VertexAI as Vertex AI (Cache Store)
    participant LLM as Gemini 1.5 Pro

    Scholar->>CacheManager: create_policy_cache(large_policy_text)
    CacheManager->>VertexAI: CachedContent.create(model, content, ttl=3600)
    VertexAI-->>CacheManager: cache_id = "projects/.../cachedContents/xxx"

    Note over VertexAI: Policy stored in Vertex memory<br/>Costs: storage only, no token re-send

    Scholar->>LLM: generate_content(user_query, cache_id=cache_id)
    Note right of LLM: Input tokens: ~50 (query only)<br/>vs. ~50,000 (full policy each time)
    LLM-->>Scholar: Grounded policy response
```

---

## 4. Protected Transactional Operation (Sentinel Guard)

Every trade must pass a deterministic compliance gate *before* being executed externally.

```mermaid
sequenceDiagram
    participant Dispatcher
    participant Sentinel
    participant Historian
    participant Executor
    participant AgentAPI as External Bank API

    Dispatcher->>Sentinel: pre_trade_check(trade_intent, user_profile)
    Note over Sentinel: Evaluate ConcentrationRule<br/>Evaluate SuitabilityRule<br/>Evaluate AgeRestrictionRule
    
    ALT Rule Violates (BLOCK)
        Sentinel->>Historian: log ACTION "BLOCK: Exceeds concentration"
        Sentinel-->>Dispatcher: ComplianceVerdict (status: BLOCK)
        Dispatcher-->>Client: Rejection Response ("Trade Blocked")
    ELSE Rule Warnings (WARN)
        Sentinel->>Historian: log ACTION "WARN: Low balance"
        Sentinel-->>Dispatcher: ComplianceVerdict (status: WARN)
        Dispatcher->>Executor: proceed_with_trade(intent)
        Executor->>AgentAPI: POST /api/v1/trade
    ELSE All Rules Pass (PASS)
        Sentinel->>Historian: log ACTION "PASS: Ready to execute"
        Sentinel-->>Dispatcher: ComplianceVerdict (status: PASS)
        Dispatcher->>Executor: proceed_with_trade(intent)
        Executor->>AgentAPI: POST /api/v1/trade
    END
```

---

## 5. Retirement Simulation (Actuarial Monte Carlo)

Shows the probabilistic path from user profile data to a confidence-band projection.

```mermaid
sequenceDiagram
    participant Dispatcher
    participant Actuarial
    participant Historian
    participant NumPy as Simulation Engine

    Dispatcher->>Actuarial: simulate(user_financial_profile)
    Actuarial->>Historian: log THOUGHT "Initializing 10,000 scenarios"
    
    loop 10,000 Sim Cycles
        Actuarial->>NumPy: Sample random returns & inflation
        NumPy-->>Actuarial: Accumulation + Decumulation Trajectory
    end

    Actuarial->>Actuarial: Compute Percentiles (p10, p50, p90)
    Actuarial->>Historian: log OBSERVATION "Success Rate: 78%"
    Actuarial-->>Dispatcher: Simulation Summary + Advice
```

---

## 6. Legacy Data Migration Flow

