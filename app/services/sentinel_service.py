import logging
from dataclasses import dataclass, field
from typing import Optional
from app.services.audit_service import historian

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ComplianceVerdict:
    """
    The output of a Sentinel compliance check.

    status: "PASS" | "WARN" | "BLOCK"
    reason: Human-readable explanation of the verdict.
    rule_name: Which rule triggered the verdict (empty for PASS).
    details: Optional dict with structured metadata for the audit trail.
    """
    status: str  # PASS | WARN | BLOCK
    reason: str = ""
    rule_name: str = ""
    details: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Compliance Rules (Deterministic — not LLM-based)
# ---------------------------------------------------------------------------

class ComplianceRule:
    """Base class for all compliance rules."""
    name: str = "BaseRule"

    def evaluate(self, trade_intent: dict, user_profile: dict) -> ComplianceVerdict:
        raise NotImplementedError


class ConcentrationRule(ComplianceRule):
    """
    No single holding should exceed a configurable percentage of the portfolio.
    Default: 10% (industry standard for diversified retail portfolios).
    """
    name = "ConcentrationLimit"

    def __init__(self, max_single_holding_pct: float = 0.10):
        self.max_pct = max_single_holding_pct

    def evaluate(self, trade_intent: dict, user_profile: dict) -> ComplianceVerdict:
        trade_value = trade_intent.get("value", 0)
        total_assets = (
            user_profile.get("financial_profile", {}).get("totalAssets", 0)
        )

        if total_assets <= 0:
            logger.warning("[Sentinel/Concentration] Total assets is zero or missing.")
            return ComplianceVerdict(
                status="WARN",
                reason="Cannot verify concentration: total assets unknown.",
                rule_name=self.name,
                details={"trade_value": trade_value, "total_assets": total_assets},
            )

        holding_pct = trade_value / total_assets
        if holding_pct > self.max_pct:
            logger.info(
                "[Sentinel/Concentration] BLOCK — %.1f%% exceeds %.1f%% limit.",
                holding_pct * 100, self.max_pct * 100,
            )
            return ComplianceVerdict(
                status="BLOCK",
                reason=(
                    f"Trade value (£{trade_value:,.0f}) represents {holding_pct:.1%} "
                    f"of total assets — exceeds {self.max_pct:.0%} concentration limit."
                ),
                rule_name=self.name,
                details={"holding_pct": holding_pct, "max_pct": self.max_pct},
            )

        return ComplianceVerdict(status="PASS")


class SuitabilityRule(ComplianceRule):
    """
    Ensures the trade's risk class is compatible with the user's declared
    risk tolerance.  Maps: aggressive ↔ high, moderate ↔ medium, conservative ↔ low.
    """
    name = "SuitabilityCheck"

    # Ordered risk levels — each value can only invest in its level or below.
    _RISK_HIERARCHY = {"conservative": 0, "low": 0, "moderate": 1, "medium": 1, "aggressive": 2, "high": 2}

    def evaluate(self, trade_intent: dict, user_profile: dict) -> ComplianceVerdict:
        user_tolerance = (
            user_profile.get("risk_profile", {}).get("risk_tolerance", "moderate")
        )
        trade_risk = trade_intent.get("risk_level", "moderate")

        user_level = self._RISK_HIERARCHY.get(user_tolerance.lower(), 1)
        trade_level = self._RISK_HIERARCHY.get(trade_risk.lower(), 1)

        if trade_level > user_level:
            logger.info(
                "[Sentinel/Suitability] BLOCK — trade risk '%s' exceeds tolerance '%s'.",
                trade_risk, user_tolerance,
            )
            return ComplianceVerdict(
                status="BLOCK",
                reason=(
                    f"Trade risk class '{trade_risk}' exceeds the user's "
                    f"declared risk tolerance '{user_tolerance}'."
                ),
                rule_name=self.name,
                details={"user_tolerance": user_tolerance, "trade_risk": trade_risk},
            )

        return ComplianceVerdict(status="PASS")


class MinimumBalanceRule(ComplianceRule):
    """
    Ensures the user retains a minimum balance after the trade.
    Default buffer: £1,000 (prevents accidental account drain).
    """
    name = "MinimumBalance"

    def __init__(self, min_balance_after_trade: float = 1000.0):
        self.min_balance = min_balance_after_trade

    def evaluate(self, trade_intent: dict, user_profile: dict) -> ComplianceVerdict:
        trade_value = trade_intent.get("value", 0)
        total_assets = (
            user_profile.get("financial_profile", {}).get("totalAssets", 0)
        )

        remaining = total_assets - trade_value
        if remaining < self.min_balance:
            logger.info(
                "[Sentinel/MinBalance] WARN — remaining balance £%.0f < £%.0f minimum.",
                remaining, self.min_balance,
            )
            return ComplianceVerdict(
                status="WARN",
                reason=(
                    f"After this trade, remaining balance would be £{remaining:,.0f} "
                    f"— below the £{self.min_balance:,.0f} safety buffer."
                ),
                rule_name=self.name,
                details={"remaining": remaining, "min_balance": self.min_balance},
            )

        return ComplianceVerdict(status="PASS")


class AgeRestrictionRule(ComplianceRule):
    """
    Blocks certain product types for users who haven't reached the eligible age.
    E.g., pension drawdown before age 55 in the UK.
    """
    name = "AgeRestriction"

    def __init__(self, min_age_for_drawdown: int = 55):
        self.min_age = min_age_for_drawdown

    def evaluate(self, trade_intent: dict, user_profile: dict) -> ComplianceVerdict:
        trade_type = trade_intent.get("type", "").lower()
        if trade_type not in ("drawdown", "pension_withdrawal"):
            return ComplianceVerdict(status="PASS")

        user_age = user_profile.get("personal_details", {}).get("age", 0)
        if user_age < self.min_age:
            logger.info(
                "[Sentinel/Age] BLOCK — user age %d < %d minimum for %s.",
                user_age, self.min_age, trade_type,
            )
            return ComplianceVerdict(
                status="BLOCK",
                reason=(
                    f"User age ({user_age}) is below the minimum age ({self.min_age}) "
                    f"required for '{trade_type}' operations."
                ),
                rule_name=self.name,
                details={"user_age": user_age, "min_age": self.min_age, "trade_type": trade_type},
            )

        return ComplianceVerdict(status="PASS")


# ---------------------------------------------------------------------------
# The Sentinel Agent
# ---------------------------------------------------------------------------

class SentinelAgent:
    """
    Pre-trade compliance gate.

    Every TRANSACTIONAL intent must pass through the Sentinel before
    the Executor can act.  The Sentinel evaluates a chain of deterministic
    rules and returns the strictest applicable verdict.

    Verdicts:
      - PASS:  All rules satisfied. Proceed to Executor.
      - WARN:  Proceed but log for human review.
      - BLOCK: Abort the trade. Explain the reason to the user.
    """

    def __init__(self, rules=None):
        self.rules = rules or [
            ConcentrationRule(),
            SuitabilityRule(),
            MinimumBalanceRule(),
            AgeRestrictionRule(),
        ]
        logger.info("[Sentinel] Initialised with %d compliance rules.", len(self.rules))

    def pre_trade_check(
        self, trade_intent: dict, user_profile: dict, conversation_id: Optional[str] = None
    ) -> ComplianceVerdict:
        """
        Runs all compliance rules in order.  Returns the first BLOCK encountered,
        or the highest-severity WARN, or PASS if everything is clear.
        """
        logger.info("[Sentinel] Starting pre-trade check | conv=%s", conversation_id)
        historian.log_step(
            session_id=conversation_id,
            agent_name="Sentinel",
            step_type="THOUGHT",
            content="Evaluating trade against compliance rules.",
            step_metadata={"trade_intent": trade_intent},
        )

        worst_warn: Optional[ComplianceVerdict] = None

        for rule in self.rules:
            verdict = rule.evaluate(trade_intent, user_profile)
            logger.debug("[Sentinel] Rule '%s' → %s", rule.name, verdict.status)

            if verdict.status == "BLOCK":
                self._log_verdict(verdict, conversation_id)
                return verdict

            if verdict.status == "WARN" and worst_warn is None:
                worst_warn = verdict

        # No BLOCK found — return WARN if any, else PASS
        final = worst_warn or ComplianceVerdict(status="PASS", reason="All compliance rules passed.")
        self._log_verdict(final, conversation_id)
        return final

    def _log_verdict(self, verdict: ComplianceVerdict, conversation_id: Optional[str]):
        """Persists the verdict to the Historian audit trail."""
        historian.log_step(
            session_id=conversation_id,
            agent_name="Sentinel",
            step_type="ACTION",
            content=f"Verdict: {verdict.status} — {verdict.reason}",
            step_metadata={
                "status": verdict.status,
                "rule_name": verdict.rule_name,
                "details": verdict.details,
            },
        )
        logger.info("[Sentinel] Final verdict: %s | rule=%s | conv=%s",
                    verdict.status, verdict.rule_name or "none", conversation_id)


# Global singleton
sentinel = SentinelAgent()
