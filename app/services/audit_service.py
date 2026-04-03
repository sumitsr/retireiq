from app import db
from app.models.audit import AgentAudit
from app.services.sse_service import sse_service
import logging

class AuditService:
    """
    Service for the Agent Audit Sentinel (The Historian).
    Provides centralized logging for the entire agentic ecosystem.
    """
    
    @staticmethod
    def log_step(session_id, agent_name, step_type, content, step_metadata=None):
        """
        Logs a granular step to the AgentAudit table.
        """
        try:
            audit_entry = AgentAudit(
                session_id=session_id,
                agent_name=agent_name,
                step_type=step_type,
                content=str(content),
                step_metadata=step_metadata
            )
            db.session.add(audit_entry)
            db.session.commit()
            
            # Broadcast to SSE in real-time
            sse_service.publish(
                session_id=session_id,
                event="agent_step",
                data={
                    "agent": agent_name,
                    "type": step_type,
                    "content": str(content)
                }
            )
            return audit_entry
        except Exception as e:
            logging.error(f"Failed to log agent audit step: {e}")
            # We don't want to fail the main transaction if auditing fails,
            # but in a bank-grade system, this would be a critical alert.
            return None

    @staticmethod
    def get_audit_trail(session_id):
        """
        Retrieves the complete history of an agent interaction for audit.
        """
        return AgentAudit.query.filter_by(session_id=session_id).order_by(AgentAudit.created_at).all()

# Single global instance for easy import
historian = AuditService()
