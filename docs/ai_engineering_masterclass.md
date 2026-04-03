# AI Engineering Masterclass: Zero to Hero (The RetireIQ Case Study)

Welcome to the **RetireIQ AI Engineering Masterclass**. This document is designed to take a developer from "Zero" to "Expert AI Engineer" by using the real-world, "Bank-Grade" architecture of RetireIQ as a living laboratory.

---

## 🏛️ Module 1: The AI Foundations (Beyond the Autocomplete)

### 1.1 What is a Large Language Model (LLM)?
At its core, an LLM is a complex statistical engine trained to predict the next "token" in a sequence. While it looks like magic, it is rooted in deep mathematical weightings (Neurons) that have "memorized" a massive corpus of human knowledge.

> [!NOTE]
> **Deep Knowledge: The Attention Mechanism**
> Think of "Attention" as the AI's ability to focus on specific words in a sentence to understand context. In the sentence *"The fixed income fund is low risk because it uses bonds"*, the word "it" has a high attention weight toward "fixed income fund," allowing the AI to understand relationships.

### 1.2 Tokens vs. Words
LLMs don't read words; they read **Tokens**. A token is usually 3-4 characters long. Understanding tokens is critical for:
- **Rate-Limiting**: Why APIs charge by the token.
- **Context Windows**: Why an LLM has a finite "memory" limit (e.g., 128k tokens).

### 1.3 LLM Roles & Temperature
In RetireIQ, we use three distinct roles to structure the conversation:
- **System**: The "Identity" (e.g., *"You are RetireIQ, a senior financial advisor..."*).
- **User**: The incoming customer prompt.
- **Assistant**: The LLM's previous responses.

**Temperature** is the "Creativity Knob." For a financial bot like RetireIQ, we keep it low (**0.0 to 0.7**) to ensure factual grounding and prevent hallucinations.

---

## 🧠 Module 2: The Vector Mind (Embeddings & RAG)

### 2.1 The Problem with Standard Search
A standard database search for "Retirement" is literal. If you have a document about "Pension Savings" but not the word "Retirement," a standard search fails.

### 2.2 What are Embeddings?
Embeddings are the secret to "Semantic Understanding." We use an embedding model (like `all-minilm`) to turn text into a **high-dimensional vector** (a list of 384 numbers).
- **Geometric Meaning**: In vector space, the word "Retirement" is mathematically "closer" to "Pension" than it is to "Banana."

### 2.3 RAG (Retrieval-Augmented Generation)
This is how we give RetireIQ "Long-Term Memory."
1. **The Ingestion**: We chunk your PDFs into small snippets.
2. **The Embedding**: We turn those snippets into vectors and store them in **pgvector**.
3. **The Retrieval**: When a user asks a question, we turn their question into a vector, find the "closest" geometry in the database, and feed those facts into the LLM prompt.

> [!TIP]
> **Why RAG?**
> RAG allows us to keep our models "Small and Smart" (Local Ollama) while still having access to millions of "Big Data" documents.

---

## 🏗️ Module 3: Multi-Agent Systems (MAS)

Moving beyond a "Single-Bot" architecture is the key to building specialized financial intelligence.

### 3.1 What is an AI Agent?
An agent is an LLM with **Autonomy** and **Tools**. While a standard chatbot just "talks," an agent can "do."
- **The Brain**: The LLM (reasoning).
- **The Hands**: Tools (Python functions, API calls, Database queries).
- **The Plan**: Chain-of-Thought (CoT) where the AI breaks down a complex request into steps.

### 3.2 The Orchestrator / Dispatcher Pattern
In RetireIQ, we don't ask one bot to do everything. We use a **Semantic Router** (The Dispatcher) to identify the user's intent.
- User: *"What's my balance?"* -> Routed to **Portfolio Agent**.
- User: *"Sell 10 shares of Apple"* -> Routed to **Transaction Agent**.
- User: *"What is a 401k?"* -> Routed to **Knowledge Agent**.

> [!IMPORTANT]
> **Deep Knowledge: Tool-use (Function Calling)**
> When an LLM "calls a tool," it doesn't actually run the code. It generates a specific JSON output (e.g., `{"function": "get_balance", "args": {"user_id": 123}}`). Your backend then intercepts this, runs the real Python function, and feeds the result back to the LLM to summarize.

---

## 🛡️ Module 4: Mission-Critical Security (The PII Proxy)

Financial data is the most sensitive information on the planet. We implement a "Bank-Grade" security layer called the **PII Proxy**.

### 4.1 The Redaction Lifecycle
To ensure zero data leaks to external LLMs, we follow a 3-step process:
1. **Redaction**: A proxy identifies names and account numbers (e.g., *"John Doe"*) and replaces them with tokens (e.g., `[PERSON_1]`).
2. **The Prediction**: The LLM works ONLY with the tokens.
3. **Re-hydration**: Before the response reaches the user, the proxy "swaps" the tokens back for the real names.

**Live Implementation: `pii_sanitizer.py`**
In [pii_sanitizer.py](../app/utils/pii_sanitizer.py), we use **Microsoft Presidio** combined with **Custom Regex Recognizers** to detect:
- **SSNs**: `\b\d{3}-\d{2}-\d{4}\b`
- **Account Numbers**: `\b[A-Z]{2,4}\d{5,12}\b`

### 4.2 Local-First Privacy
By using **Ollama** locally, we keep the data within your machine's biological boundary. If we were to use a Cloud LLM (OpenAI/Gemini), the PII Proxy becomes our secondary firewall.

**Live Execution: `llm_service.py`**
In [llm_service.py](../app/services/llm_service.py), every single LLM call is "wrapped" in the sanitizer:
```python
# From the live code
sanitizer.clear_mapping()
anonymized_profile = sanitizer.sanitize_profile_to_string(user_profile)
sanitized_message, message_mapping = sanitizer.sanitize_text(message)
```

---

## ⚖️ Module 5: Evaluation (How do we know it's good?)

In traditional coding, `2 + 2` is always `4`. In AI, the output is "Probabilistic" (meaning it varies).

### 5.1 The "Hallucination" Problem
A hallucination is when an LLM confidently states a fact that is false (e.g., *"The fixed income fund yield is 500%"*). 

### 5.2 RAG Evaluation
To prevent this, we use a **Fact-Checker Agent**. Its only job is to compare the LLM's answer against the **Source Policy** from our vector database. If the answer isn't in the source, the response is blocked.

> [!TIP]
> **Zero-Fault Culture**
> Expert AI Engineering is not about making the bot "smarter"—it's about making the bot "safer."

---

## 🚀 Module 6: The Path to Enterprise Scale

### 6.1 Transitioning to the Cloud
While we develop locally with **Ollama**, a production system needs the massive scale of **Google Cloud (GCP)**.
- **Local Dev**: Faster, cheaper, 100% private.
- **Enterprise Prod**: Vertex AI, Gemini 1.5 Pro, and Cloud Run for global availability.

---

*This concludes the core curriculum. RetireIQ is your sandbox to practice these implementations.*
