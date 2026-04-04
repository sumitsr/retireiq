import logging
import json
from datetime import datetime
from typing import Dict, Any, List
from app import db
from app.models.audit import AgentAudit

logger = logging.getLogger(__name__)

class ReportingService:
    """
    The Compliance Sentinel: Generates regulatory audit reports.
    FCA/FINRA/MiFID II compliant immutable record extraction.
    """

    def __init__(self):
        logger.info("[Reporting] Compliance Service initialized.")

    def generate_regulatory_report(self, session_id: str) -> Dict[str, Any]:
        """
        Exports the full agent reasoning chain for a given conversation.
        Includes internal thoughts, tool observations, and final responses.
        """
        logger.info("[Reporting] Generating compliance manifest | session=%s", session_id)
        
        # 1. Fetch all audit steps
        audit_steps = AgentAudit.query.filter_by(session_id=session_id).order_by(AgentAudit.created_at.asc()).all()
        
        if not audit_steps:
            logger.warning("[Reporting] No audit data found for session %s", session_id)
            return {"status": "NOT_FOUND", "session_id": session_id, "manifest": []}

        # 2. Build the Manifest
        manifest = [step.to_dict() for step in audit_steps]
        
        # 3. Add Regulatory Header
        report = {
            "version": "1.0-PROD",
            "compliance_standard": ["MiFID II", "GDPR", "FCA", "FINRA"],
            "generation_timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "agent_count": len(set(s.agent_name for s in audit_steps)),
            "step_count": len(audit_steps),
            "manifest": manifest,
            "integrity_hash": self._generate_report_hash(manifest) # Placeholder for signing
        }
        
        return report

    def _generate_report_hash(self, manifest: List[Dict[str, Any]]) -> str:
        """
        Placeholder for SHA-256 integrity check to ensure audit immutability.
        In production, this would be signed with a hardware security module (HSM).
        """
        import hashlib
        manifest_str = json.dumps(manifest, sort_keys=True)
        return hashlib.sha256(manifest_str.encode()).hexdigest()

# Global singleton
reporting_service = ReportingService()
