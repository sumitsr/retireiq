# Enterprise-Grade PII Sanitization

For modern financial-tech applications handling LLM integration, data privacy is non-negotiable. RetireIQ employs a strict barrier between our server environments and any third-party APIs like external Large Language Models.

We ensure that Protected Health Information (PHI), Personally Identifiable Information (PII), or Sensitive Financial Data is never transmitted externally.

## Core Responsibilities
The **PII Sanitizer Layer** acts as a bi-directional transparent proxy filter mapping text entities to deterministic variables immediately prior to LLM query routing. 

## Technical Implementation Workflow

1. **Detection Phase (Entity Recognition)**
   The system utilizes robust Named Entity Recognition (NER) (e.g., integrating Presidio or custom spaCy logic) alongside tightly bounded regex to capture bank-specific formats, identifying:
   - First and Last Names
   - Social Security Numbers (SSN)
   - Account / Routing Numbers
   - Portfolios, Phone numbers, Physical Addresses, Identifiable Email addresses.

2. **Redaction Phase (Tokenization)**
   Identified data blocks are substituted with generic but categorized markers, and their true values are inserted into a fast ephemeral key-value map cache mapping the token to the real string for this specific transaction.
   - *Original*: "John Doe wants to check the routing number 123456789."
   - *To LLM*: "[PERSON_0] wants to check the routing number [ROUTING_NUMBER_0]."

3. **External Transmission**
   The LLM provider reads the fully redacted context and builds a reasonable response utilizing identical token placement logic.
   - *LLM Response*: "I have securely looked up the account for [PERSON_0] matching [ROUTING_NUMBER_0]."

4. **De-Sanitization Phase (Re-hydration)**
   Before the HTTP response cycles back through the Flask API layer to the end user client, the PII Sanitizer executes a reverse map parsing. It searches for tokens and replaces them identically with the original data stored in our private ephemeral map.
   - *Final User View*: "I have securely looked up the account for John Doe matching 123456789."

### Resulting Compliance 
This architecture guarantees strict enterprise compliance measures for data locality, anonymizing conversational interfaces and ensuring our relational data models never inadvertently bleed across untrusted API boundaries while retaining completely natural conversation UX continuity.
