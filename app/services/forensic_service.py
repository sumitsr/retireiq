import logging
from typing import Dict, Any, Optional
from app.services.audit_service import historian

logger = logging.getLogger(__name__)

class ForensicAgent:
    """
    The Forensic Agent: Anomaly Detection & Fraud Prevention.
    
    This agent monitors the 'Intent Stream' and user activity to detect 
    patterns of panic, fraud, or credential-stuffing behavior.
    """

    def __init__(self):
        logger.info("[Forensic] Agent initialized.")

    def analyze_intent(self, intent_data: Dict[str, Any], user_profile: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
        """
        Analyzes the current intent for anomalous indicators.
        Returns a forensic report: {"status": "GREEN" | "YELLOW" | "RED", "reasons": []}
        """
        logger.info("[Forensic] Analyzing intent for anomalies | conv=%s", conversation_id)
        
        self._log_thought(conversation_id, "Running behavior-signature analysis on incoming intent logic.")

        reasons = []
        status = "GREEN"

        # 1. Anomaly: Mass Withdrawal
        trade_value = intent_data.get("trade_value", 0)
        portfolio_total = user_profile.get("financial_profile", {}).get("total_assets", 1000000)
        
        if trade_value > (portfolio_total * 0.5): # Over 50% liquidation
            reasons.append("HIGH_VELOCITY_LIQUIDATION: Request exceeds 50% of total portfolio value.")
            status = "RED"

        # 2. Anomaly: Sudden Risk Shift
        current_risk = user_profile.get("risk_profile", {}).get("tolerance", "LOW")
        intent_sub = intent_data.get("sub_intent", "").lower()
        
        if current_risk == "CONSERVATIVE" and "aggressive" in intent_sub:
            reasons.append("RISK_VOLATILITY: Unexpected shift from CONSERVATIVE to AGGRESSIVE investment sub-intent.")
            status = "YELLOW"

        if status != "GREEN":
            self._log_observation(conversation_id, f"Forensic Alert: {status} status. Reasons: {reasons}")
        else:
            self._log_observation(conversation_id, "Forensic scan complete. No high-velocity or risk-profile anomalies detected.")

        return {
            "status": status,
            "reasons": reasons,
            "risk_score": 0.9 if status == "RED" else (0.4 if status == "YELLOW" else 0.1)
        }

    # -----------------------------------------------------------------------
    # Private — Audit logging
    # -----------------------------------------------------------------------

    def _log_thought(self, conversation_id, content):
        historian.log_step(
            session_id=conversation_id,
            agent_name="Forensic",
            step_type="THOUGHT",
            content=content,
        )

    def _log_observation(self, conversation_id, content):
        historian.log_step(
            session_id=conversation_id,
            agent_name="Forensic",
            step_type="OBSERVATION",
            content=content,
        )

# Global singleton
forensic = ForensicAgent()
