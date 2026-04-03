# AI Engineering Masterclass: Zero to Hero (The RetireIQ Case Study)

Welcome to the **RetireIQ AI Engineering Masterclass**. This document is designed to take a developer from "Zero" to "Expert AI Engineer" by using the real-world, "Bank-Grade" architecture of RetireIQ as a living laboratory.

---

## 🏛️ Module 1: The AI Foundations (The Vector Transformation)

### 1.1 Beyond the Autocomplete: The Attention Mechanism
While many see LLMs as simple word predictors, an Expert AI Engineer understands the **Transformer Architecture**. The "Secret Sauce" is **Multi-Head Attention**.

**RetireIQ Implementation: LLM Roles**
In RetireIQ, we use three distinct roles to structure every single prompt:
- **System**: The "Identity" (e.g., *"You are RetireIQ, a senior financial advisor..."*).
- **User**: The incoming customer prompt.
- **Assistant**: The LLM's previous responses (history).

> [!NOTE]
> **Expert Concept: Q, K, V (Query, Key, Value)**
> Think of Attention like a retrieval system. 
> 1. **Query ($Q$)**: What the current word is looking for.
> 2. **Key ($K$)**: What other words in the sentence represent.
> 3. **Value ($V$)**: The actual information to "attend" to.
> 
> The model calculates a "Dot Product" between $Q$ and $K$ to determine weight. If you're analyzing a loan application, the word "Income" ($Q$) will have a high Weight toward the numerical value "$150,000$" ($K$), allowing the AI to bind the concept to the data.

### 1.2 The Token Lifecycle
LLMs digest **Tokens**, not words. We use the **Byte-Pair Encoding (BPE)** algorithm to break text into sub-word units.
- **Efficiency**: "Retirement" might be 1 token, but "RetireIQ-Masterclass" might be 4.
- **Context Window**: In RetireIQ, we monitor the context limits (e.g. 128k for GPT-4o) to prevent "Context Overflow," which leads to the model "forgetting" the beginning of the conversation.

### 1.3 Sampling Parameters: Shaping the Probability Distribution
When the LLM predicts the next token, it produces **Logits** (raw scores). We use sampling to select the final token from this distribution:

### 1.3 Sampling Parameters: Shaping the Probability Distribution
When the LLM predicts the next token, it produces **Logits** (raw scores). We use sampling to select the final token from this distribution:

| Parameter | Mathematical Impact | RetireIQ Usage (The Why) |
| :--- | :--- | :--- |
| **Temperature ($T$)** | Divides logits before Softmax ($score_i / T$). | **$T=0$ (Greedy)**: Used for intent extraction. **$T=0.7$**: Our "Chat Standard" for human-like dialogue. |
| **Top-P (Nucleus)** | Dynamic threshold. Sums tokens until cumulative mass is $P$. | Preferred for RetireIQ because it **adapts** to confidence. If the model is 99% sure, the pool is tiny. |

#### 🌡️ Deep Dive: The Temperature Decision Matrix
In RetireIQ, we don't just "pick a number." We align $T$ with the **Cognitive Load** of the task:

- **Scenario A: $T=0.0$ (The "Robot" - Data Extraction)**
    - *Usage*: When asking the AI to "Extract the account number from this text."
    - *Why*: We need 100% precision. At $T=0$, the AI will **never** vary its answer. It always picks the mathematically certain token.
- **Scenario B: $T=0.3$ (The "Analyst" - Summarization)**
    - *Usage*: Summarizing a 50-page investment policy.
    - *Why*: We want the summary to sound professional (not repetitive), but we cannot risk the AI "inventing" new financial terms. This adds a tiny bit of linguistic flavor without sacrificing grounding.
- **Scenario C: $T=0.7$ (The "Advisor" - RetireIQ Chat)**
    - *Usage*: General conversation with a user about their goals.
    - *Why*: **The Human Factor**. $T=0.7$ allows the model to use natural sentence structures and varied vocabulary. It makes RetireIQ feel like a person, not a database interface, while staying within the "Safe Sampling" boundary.
- **Scenario D: $T=1.0+$ (The "Poet" - Brainstorming)**
    - *Usage*: "Give me 10 unique names for a new retirement fund."
    - *Why*: We want the model to explore the "Long Tail" of its vocabulary. High temperature flattens the probability, allowing "surprising" tokens to be selected.

> [!IMPORTANT]
> **Expert Pro-Tip: Hallucination Risk**
> As $T$ increases, the probability of **Hallucination** increases linearly. In "Bank-Grade" systems, we rarely exceed $0.7$ to ensure that creativity never overrides factual integrity.

---

## 🧠 Module 2: The Vector Mind (Geometry vs. Keywords)

### 2.1 The Case Study: "Pension" vs. "Retirement"
A standard database search for "Retirement" is literal. If you have a document about "Pension Savings" but not the word "Retirement," a standard search fails. This iswhy RetireIQ uses **Semantic (Geometric) Search**.

### 2.2 Embeddings & High-Dimensional Space
We use models like `all-minilm` to transform text into a **high-dimensional vector** (e.g. 384 numbers). 
- **The Manifold**: Think of the AI's mind as a map. "Pension" and "401k" are geometrically adjacent (low distance), even if they share zero characters.

### 2.3 RAG (Retrieval-Augmented Generation)
This is how we give RetireIQ "Long-Term Memory."
1. **The Ingestion**: We chunk your PDFs into small snippets.
2. **The Embedding**: We turn those snippets into vectors and store them in **pgvector**.
3. **The Retrieval**: When a user asks a question, we turn their question into a vector and find the "closest" geometry in the database.

> [!TIP]
> **RetireIQ Rationale: Why RAG?**
> RAG allows us to keep our models "Small and Smart" (Local Ollama) while still having access to millions of "Big Data" documents.

### 2.4 Search Engineering: HNSW & Vector Indexing
Searching through 1 million vectors linearly is $O(n)$—too slow for a chatbot. Expert systems use **HNSW (Hierarchical Navigable Small Worlds)**.

**Live Implementation: `knowledge_service.py`**
In [/knowledge_service.py](../app/services/knowledge_service.py), we handle these embeddings and vector storage logic.

---

## 🏗️ Module 3: Multi-Agent Systems (The Collaborative Brain)

Moving beyond a "Single-Bot" architecture is the key to building specialized financial intelligence. We use a **MAS (Multi-Agent System)** to distribute complexity.

### 3.1 The ReAct Pattern (Reason + Act)
In RetireIQ, our agents don't just guess; they perform **ReAct** loops. 

### 3.2 The Orchestrator / Dispatcher Pattern
We don't ask one bot to do everything. We use a **Semantic Router** (The Dispatcher) to identify the user's intent:
- User: *"What's my balance?"* -> Routed to **Portfolio Agent**.
- User: *"Sell 10 shares of Apple"* -> Routed to **Transaction Agent**.
- User: *"What is a 401k?"* -> Routed to **Knowledge Agent**.

> [!IMPORTANT]
> **RetireIQ Rationale: Why Dispatch?**
> This dispatcher approach prevents "Instruction Bleed." A Knowledge Agent doesn't need to know how to sell stocks, and a Transaction Agent doesn't need to know the definition of a 401k.

### 3.3 Advanced Knowledge: Tool-use (Function Calling)
When an LLM "calls a tool," it generates a specific JSON output based on a schema we provide. 

---

## 🛡️ Module 4: Mission-Critical Security (The PII Proxy)

### 4.1 The De-identification Lifecycle (The RetireIQ Firewall)
To ensure zero data leaks to external LLMs (OpenAI/Azure), we solve the "Bank Data Paradox" with a 3-step transformation:

1. **Anonymization (Entry)**: Our proxy uses **NER (Named Entity Recognition)** models and **Custom Regex** to identify identities.
    - **SSNs**: `\b\d{3}-\d{2}-\d{4}\b`
    - **Account Numbers**: `\b[A-Z]{2,4}\d{5,12}\b`
2. **The Prediction (External)**: The LLM works *only* with surrogate tokens like `[CLIENT_NAME_1]`.
3. **Re-hydration (Exit)**: Before the response reaches the user, the proxy "swaps" the tokens back using a secure, local mapping.

### 4.2 Local-First Privacy (The Ollama Wall)
By using **Ollama** locally, we create a "Biological Boundary." Data stays on your machine.

**Live Implementation: `pii_sanitizer.py`**
In [/pii_sanitizer.py](../app/utils/pii_sanitizer.py), we use **Microsoft Presidio** to handle this redaction logic.

---

## ⚖️ Module 5: Evaluation (The Hallucination Firewall)

### 5.1 The Hallucination Case Study
A hallucination is when an LLM confidently states a fact that is false (e.g., *"The fixed income fund yield is 500%"*). In RetireIQ, we use the **RAGAS (RAG Assessment)** framework to measure performance.

### 5.2 Expert Tactic: Fact-Checking Agents
To ensure "Bank-Grade" accuracy, we use a secondary **Validator Agent**. It receives the response and the source documents, then performs a "Cross-Check". 

---

## 🚀 Module 6: The Path to Enterprise Scale (GCP & Vertex AI)

### 6.1 Scaling RetireIQ with Vertex AI
While we develop locally with **Ollama**, a production system needs the massive scale of **Google Cloud (GCP)**.
- **Context Caching**: For massive bank policies, we cache the vector state in Vertex AI to reduce latency.
- **Controlled Output**: We enforce **JSON Schema** to ensure 100% reliable system integration.

---

## 🧪 Module 7: AI Testing & Evaluation (The Reliability Barrier)

Traditional software is **Deterministic**. AI is **Probabilistic**. This is why RetireIQ treats **95% Code Coverage** as a "Hard Requirement" for production.

### 7.1 The Power of Mocking
To achieve our high coverage, we use `unittest.mock` to simulate LLM responses. This allows us to test how RetireIQ handles:
1. **Valid JSON Intent**: Does the system call the right agent?
2. **Malformed JSON**: Does the system fail gracefully?
3. **Empty Responses**: Does the system ask the user for clarification?

> [!IMPORTANT]
> **The Golden Rule of AI Engineering**
> "If you can't test it, don't deploy it." RetireIQ's stability is built on our **Testing Suite**, not just the model's intelligence.

---

*This concludes the core curriculum. RetireIQ is your sandbox to practice these implementations.*
