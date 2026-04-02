# Application Sequence Diagrams

The following flows show the lifecycle of typical requests in the RetireIQ system.

## 1. Chat Execution Flow with RAG & Conversational Memory

This flow demonstrates the end-to-end multi-turn conversation layer.

```mermaid
sequenceDiagram
    participant User
    participant API as Flask API
    participant Mem as Memory DB
    participant PII as PII Sanitizer
    participant RAG as Retrieval Engine
    participant LLM as External LLM

    User->>API: POST /chat {user_id, prompt}
    API->>Mem: Fetch Historical Context Limit N
    Mem-->>API: Returns Array of historical messages
    API->>RAG: Retrieve relevant knowledge base docs for prompt
    RAG-->>API: Appends internal documentation payload
    API->>PII: Initiate outgoing PII wipe (Prompt + Context + History)
    PII-->>API: Redacted/Cleaned Payload (Names -> [PERSON_1])
    API->>LLM: Generate conversational AI response
    LLM-->>API: Text Answer (Includes tokens e.g. [PERSON_1])
    API->>PII: De-sanitize/Re-hydrate LLM response
    PII-->>API: Original Context Injected Answer
    API->>Mem: Save new prompt and response pair to relational DB
    API-->>User: 200 OK - Return final output
```

## 2. Legacy Data Migration Flow

This sequence visualizes the shift from unstructured JSONs to structured SQL.

```mermaid
sequenceDiagram
    participant CLI
    participant Script as Migration Script
    participant JSON as old_data.json
    participant DB as Postgres Relational DB

    CLI->>Script: Run `flask seed db`
    Script->>JSON: Read and parse JSON content
    loop For Each Object Instance
        Script->>Script: Perform data transformations & map to SQLAlchemy Models
        Script->>DB: Add to active session (Batch INSERT)
    end
    DB-->>Script: Acknowledge successful commit
    Script-->>CLI: Print Migration Success message
```
