# Conversational Memory

The **Conversational Memory** component solves a fundamental problem with Large Language Models: LLMs are inherently stateless. Out of the box, they don't remember what was said in previous messages. 

To create a natural, multi-turn "bank-grade customer service chatbot," we have to explicitly provide the model with the history of the conversation every single time we send a new prompt. The Conversational Memory component is responsible for orchestrating this continuous state.

## How it works in RetireIQ

RetireIQ implements a **Dual-Layer Memory** architecture:

### 1. Short-Term History (The Transcript)
Every user message and AI response is saved in the `messages` table.
- **Cycle**: When a new query arrives, the `MemoryService` retrieves the last 10 messages for that `session_id`.
- **Purpose**: Provides immediate conversational context ("What did we just talk about?").

### 2. Long-Term Facts (The UserMemory)
This is the "Brain" of the system.
- **Extraction**: A background task periodically runs the **Analyst Agent** over the transcript. It extracts persistent financial facts (e.g., "User has a daughter named Sarah," "User plans to buy a house in 2028").
- **Storage**: Facts are stored in the `user_memories` table, linked to the `User` model.
- **RAG Integration**: These facts are injected into the System Prompt for every future session, ensuring the AI "knows" the user across different days and devices.

### 3. Assembling the Prompt Array
The `llm_service` combines:
1. **System Prompt**: Core personality + User Facts (Long-term).
2. **Context**: Relevant policy snippets from the Scholar (RAG).
3. **History**: The last few transcript turns (Short-term).
4. **Current Query**: The user's latest message.

## Status: 🧠 **v1.0 Production-Ready**

RetireIQ uses a background **Summarization-into-Facts** pattern to maintain a persistent user profile without token bloat.

### 4. Pruning and Summarization
To manage token costs and latency:
- **Rolling Window**: Only the most recent $N$ messages are sent.
- **Summarization**: Older messages are compressed into a "contextual summary" by the `MemoryService` if the transcript exceeds 2,000 tokens.

---


