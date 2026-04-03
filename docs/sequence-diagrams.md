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

## 4. Legacy Data Migration Flow

This sequence visualizes the historical shift from unstructured JSONs to structured SQL.

```mermaid
sequenceDiagram
    participant CLI
    participant Script as Migration Script
    participant JSON as old_data.json
    participant DB as PostgreSQL Relational DB

    CLI->>Script: Run `flask seed db`
    Script->>JSON: Read and parse JSON content
    loop For Each Object Instance
        Script->>Script: Perform data transformations & map to SQLAlchemy Models
        Script->>DB: Add to active session (Batch INSERT)
    end
    DB-->>Script: Acknowledge successful commit
    Script-->>CLI: Print Migration Success message
```
