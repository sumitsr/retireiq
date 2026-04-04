# Enterprise-Grade PII Sanitization: The Guardian Pattern

## Status: 🛡️ **v1.0 Production-Ready (Bank-Grade)**

RetireIQ implements a dual-layer PII sanitization strategy:
1.  **The Guardian (Local)**: Symmetrical anonymization using Microsoft Presidio.
2.  **The Shield (LLM-Gate)**: Intent-based safety classification.

For modern fintech applications, data privacy is non-negotiable. RetireIQ employs a **Guardian Agent** (PIISanitizer) that acts as a bi-directional transparent proxy between our secure server and external LLM providers.

## Core Responsibilities
The **PII Sanitizer Layer** ensures that Protected Health Information (PHI), Personally Identifiable Information (PII), and Sensitive Financial Data (Account numbers) never leave the local environment.

## The 4-Phase Lifecycle

### 1. Detection (Named Entity Recognition)
The system uses **Microsoft Presidio** backed by **spaCy** (`en_core_web_sm`) to identify sensitive entities:
- **Identity**: Person names, Email addresses, Phone numbers.
- **Financial**: IBANs, Credit Card numbers, Account IDs.
- **Location**: Physical addresses, Zip codes.

### 2. Redaction (The Ghost Map)
Identified entities are substituted with generic, categorized tokens (e.g., `<PERSON_0>`). The original value is stored in an ephemeral, per-request **Ghost Map**.
- **Input**: "Transfer £500 to Alice Smith."
- **Redacted**: "Transfer £500 to <PERSON_0>."

### 3. External Processing
The LLM (Gemini, GPT-4, or Ollama) processes the redacted text. It never "sees" Alice Smith, only contextually aware tokens.
- **LLM Output**: "I have prepared the transfer of £500 to <PERSON_0>."

### 4. De-anonymization (Re-hydration)
Before the response reaches the user, the PIISanitizer parses the output, matching tokens against the **Ghost Map** to restore the original values.
- **Final Result**: "I have prepared the transfer of £500 to Alice Smith."

## Security & Compliance
- **Session Isolation**: The Ghost Map is purged at the start of every request cycle to prevent cross-user data leakage.
- **In-Memory Only**: Mappings are never written to disk, databases, or logs.
- **Audit-Safe**: The Historian logs the *fact* that sanitization occurred, but never the original sensitive strings.

> [!IMPORTANT]
> This "Guardian" pattern allows RetireIQ to leverage high-power cloud LLMs while maintaining a bank-grade security posture.

