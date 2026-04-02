# Conversational Memory

The **Conversational Memory** component solves a fundamental problem with Large Language Models: LLMs are inherently stateless. Out of the box, they don't remember what was said in previous messages. 

To create a natural, multi-turn "bank-grade customer service chatbot," we have to explicitly provide the model with the history of the conversation every single time we send a new prompt. The Conversational Memory component is responsible for orchestrating this continuous state.

## How it works in RetireIQ

### 1. Persistence (State Management)
Every time a user asks a question and the AI replies, those two messages are saved as a "turn" inside a dedicated table in the PostgreSQL database (tied to a unique session and user identifier).

### 2. Context Window Management
When a user asks a *new* follow-up question (e.g., "Can you elaborate on that?"), the Flask API first calls the Conversational Memory component. The Memory component queries the database for the last `N` messages belonging to that specific session. 

### 3. Assembling the Prompt Array
The Memory component formats those past messages into a continuous, ordered context array (for instance: `["User: How much is in my 401k?", "AI: You have $50,000.", "User: Can you elaborate on that?"]`) and hands it to the RAG Orchestrator / LLM. 

### 4. Pruning and Summarization (Advanced Scalability)
If a conversation goes on for 50+ messages, sending the entire history would consume too many tokens, increasing latency and exceeding the LLM's context limit. Our conversational memory layer handles this by automatically "pruning" the history (e.g., keeping only the 5 most recent relevant turns) or by generating a rolling summary of the older conversation to keep the token payload lightweight and cost-effective.

**In summary:** The Conversational Memory is the critical storage and retrieval mechanism that gives our chatbot the illusion of memory, allowing users to ask follow-up queries naturally without having to repeatedly restate all their prior context.
