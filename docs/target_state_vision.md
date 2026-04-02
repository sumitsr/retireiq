# Target State Architecture Vision

This document outlines the world-class final state architecture for RetireIQ. It encompasses all modular steps from customer interaction through intent resolution, security, RAG, and LLM processing.

## Enterprise AI Workflow Architecture

```mermaid
flowchart TD
    %% Styling
    classDef default fill:#f8fafc,stroke:#cbd5e1,stroke-width:1px,color:#334155;
    classDef user fill:#edf2f8,stroke:#3b82f6,stroke-width:2px,color:#1e3a8a,rx:4,ry:4;
    classDef orchestration fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#581c87,rx:4,ry:4;
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#991b1b,rx:4,ry:4;
    classDef ai fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#065f46,rx:4,ry:4;
    classDef data fill:#ffedd5,stroke:#f97316,stroke-width:2px,color:#9a3412,rx:4,ry:4;
    classDef tasks fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#3730a3,rx:4,ry:4;

    %% Nodes
    User["🧑‍💻 Customer / Client App"]:::user

    subgraph Edge ["Edge & Entry"]
        Gateway["🌐 API Gateway & Auth"]:::orchestration
    end

    subgraph Orchestration ["Workflow Orchestration"]
        Router{"🧠 Intent Resolution"}:::ai
        Memory[("📚 Conversational State Db")]:::data
    end

    subgraph Agents ["Task Execution Layer"]
        T1["💸 Transaction Agent"]:::tasks
        T2["📊 Portfolio Agent"]:::tasks
        RAGTask["📖 Knowledge Agent"]:::tasks
    end

    subgraph RAG ["RAG Learning Ecosystem"]
        Retriever["🔍 Semantic Retriever"]:::ai
        VectorDB[("🗄️ Vector Database")]:::data
        Ingestion["⚙️ Document Ingestion"]:::orchestration
        
        Ingestion -->|Embeds & Upserts| VectorDB
        Retriever <-->|Queries| VectorDB
    end

    subgraph Security ["PII Sanitization Firewall"]
        Redact["🛡️ PII Redaction Proxy"]:::security
        DeRedact["🔓 PII Re-hydrator"]:::security
    end

    subgraph Core ["Intelligence Core"]
        LLM["🤖 Large Language Model"]:::ai
    end

    %% Workflow Connections
    User <-->|Encrypted HTTP| Gateway
    Gateway -->|Validated Request| Router
    Router <-->|Read / Update| Memory

    %% Intent Routing
    Router -->|Trade| T1
    Router -->|Balance| T2
    Router -->|Policy| RAGTask

    %% RAG Fetch
    RAGTask <-->|Fetch Context| Retriever

    %% Sanitization Boundary
    T1 & T2 & RAGTask -->|Raw Prompt + Context| Redact
    Redact -->|Masked Prompt| LLM
    LLM -->|Masked Prediction| DeRedact
    DeRedact -->|Cleaned Response| Gateway
```

## Workflows Demystified

1. **Customer Interaction**: The user submits a natural language request via the app.
2. **Intent Resolution Engine**: A fast, low-latency classifier assesses if the user wants to trade, verify a balance, or just ask a policy question. It delegates the prompt to the correct **Task Agent**.
3. **Conversational Learning**: During intent routing, user preferences and immediate past conversational states are injected so the bot remembers if the user is upset, what they just asked, and their risk tolerance.
4. **Task Agents**: Dedicated workers handle specific logic. The `Knowledge Agent` specifically taps into the **RAG-Based Learning Ecosystem** to augment its prompt with the bank's latest policies.
5. **Continuous RAG Learning**: A background mechanism continuously embeds new Bank policy PDFs/documents so the vector database never goes stale. 
6. **PII Sanitization**: Before *any* context hits an external LLM, the firewall strips out numbers and names, mapping them in ephemeral memory. The LLM generates a mathematically optimal response using tokens, which the De-Redaction proxy rebuilds into a legible sentence for the Gateway to return.

---

> [!NOTE]  
> ## Enhancements Backlog (Gap Analysis)
> To achieve this final state from our current setup, the following enhancements need to be queued for implementation:
> 
> - [ ] **Implement Intent Resolution Layer**: Currently, we have a monolithic RAG router. We need a semantic router (langchain or native NLP) to dynamically choose *which* tool/agent to invoke based on the user's prompt.
> - [ ] **Upgrade Memory to 'Learning'**: Evolve the existing `Chat Memory` from standard N-turn tracking to a profile-learning model (extracting traits and saving long-term user facts to their DB profile).
> - [ ] **Vector Database Standup**: Ensure we have a dedicated Vector store integration (like PgVector or Pinecone) alongside an ingestion cron-job for "continuous learning", so policies are automatically updated without manual application deployments.
> - [ ] **Agentic Isolation**: Split our monolithic logic into distinct Agents (e.g., Transaction, Portfolio, Knowledge).
