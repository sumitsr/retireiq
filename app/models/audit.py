from app import db
from datetime import datetime
from sqlalchemy import JSON
import uuid

class AgentAudit(db.Model):
    """
    High-Fidelity Agent Audit Sentinel (The Historian).
    Records every granular step of the multi-agent reasoning process.
    """
    __tablename__ = 'agent_audit'

    id = db.Column(db.Integer, primary_key=True)
    # session_id links all steps of a single user request/conversation
    session_id = db.Column(db.String(36), index=True, nullable=False)
    # The name of the agent performing the step (e.g. Dispatcher, Scholar, Analyst)
    agent_name = db.Column(db.String(50), nullable=False)
    # The type of step (THOUGHT, ACTION, OBSERVATION, RESPONSE)
    step_type = db.Column(db.String(20), nullable=False)
    # The raw content of the step
    content = db.Column(db.Text, nullable=False)
    # Technical metadata (e.g. model_name, tokens, latency, tool_id)
    step_metadata = db.Column(JSON, default={})
    # Precision timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, session_id, agent_name, step_type, content, step_metadata=None):
        self.session_id = str(uuid.uuid4()) if not session_id else str(session_id)
        self.agent_name = agent_name
        self.step_type = step_type
        self.content = content
        self.step_metadata = step_metadata if step_metadata else {}

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "step_type": self.step_type,
            "content": self.content,
            "metadata": self.step_metadata,
            "timestamp": self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<AgentAudit {self.agent_name}:{self.step_type} ({self.session_id})>"
