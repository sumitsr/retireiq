import logging
from typing import Dict, Any, Optional, List
from app.services.llm_service import call_vertex_ai_api
from app.services.audit_service import historian

logger = logging.getLogger(__name__)

class VisionAgent:
    """
    The Document Ingestion Agent (The Vision).
    Uses multimodal LLMs (Gemini 1.5 Pro) to extract financial structured data from images/PDFs.
    """
    
    SYSTEM_PROMPT = """
    You are the RetireIQ Vision Agent. Your goal is to extract structured financial data 
    from the provided document (Image or PDF).
    Identify:
    1. Institution Name
    2. Document Date
    3. Account Type (Pension, ISA, 401k, etc.)
    4. Current Balance (Amount and Currency)
    5. List of Holdings (Name, Units, Value)

    Output ONLY a JSON object:
    {
        "institution": "...",
        "date": "...",
        "account_type": "...",
        "total_balance": 0.00,
        "holdings": [{"name": "...", "units": 0, "value": 0.00}]
    }
    """

    def ingest_document(self, base64_image: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Runs multimodal extraction on a document byte string or base64."""
        logger.info("[The Vision] Ingesting document | conv=%s", conversation_id)
        
        if conversation_id:
            historian.log_step(
                session_id=conversation_id,
                agent_name="Vision",
                step_type="THOUGHT",
                content="OCRing and parsing uploaded document for financial entities."
            )

        # Call Gemini 1.5 Pro via Vertex AI multimodal
        raw_json = call_vertex_ai_api(
            prompt=self.SYSTEM_PROMPT,
            model_name="gemini-1.5-pro",
            temperature=0.0, # Deterministic extraction
            attachments=[base64_image]
        )
        
        # In a real system, we'd use PII Sanitizer on the output before logging 
        # (though here the Vision output is for the bot's internal use)
        
        try:
            import json
            import re
            match = re.search(r"\{.*\}", raw_json, re.DOTALL)
            parsed = json.loads(match.group()) if match else {}
            
            if conversation_id:
                historian.log_step(
                    session_id=conversation_id,
                    agent_name="Vision",
                    step_type="OBSERVATION",
                    content=f"Extracted {parsed.get('account_type')} statement from {parsed.get('institution')}.",
                    step_metadata=parsed
                )
            
            logger.info("[The Vision] Extraction successful | institution=%s", parsed.get("institution"))
            return parsed
        except Exception as e:
            logger.error("[The Vision] Extraction failed to parse: %s", e)
            return {"error": "Failed to extract data from document"}

# Singleton
vision_agent = VisionAgent()
