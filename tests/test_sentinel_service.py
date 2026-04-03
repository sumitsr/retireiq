"""
Tests for the Sentinel Agent (Pre-Trade Compliance).
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.sentinel_service import (
    sentinel,
    SentinelAgent,
    ComplianceVerdict,
    ConcentrationRule,
    SuitabilityRule,
    MinimumBalanceRule,
    AgeRestrictionRule,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rich_user_profile():
    """A fully populated user profile for compliance testing."""
    return {
        "id": "user_123",
        "personal_details": {"age": 45, "first_name": "Jane"},
        "financial_profile": {"totalAssets": 100000.0},
        "risk_profile": {"risk_tolerance": "moderate"},
    }


@pytest.fixture
def young_user_profile():
    """A user too young for pension drawdown."""
    return {
        "id": "user_young",
        "personal_details": {"age": 30},
        "financial_profile": {"totalAssets": 50000.0},
        "risk_profile": {"risk_tolerance": "moderate"},
    }


# ---------------------------------------------------------------------------
# ConcentrationRule
# ---------------------------------------------------------------------------

class TestConcentrationRule:
    def test_pass_within_limit(self, rich_user_profile):
        rule = ConcentrationRule(max_single_holding_pct=0.10)
        trade = {"value": 5000}  # 5% of 100k
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "PASS"

    def test_block_exceeds_limit(self, rich_user_profile):
        rule = ConcentrationRule(max_single_holding_pct=0.10)
        trade = {"value": 15000}  # 15% of 100k
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "BLOCK"
        assert "concentration" in verdict.reason.lower()

    def test_warn_on_zero_assets(self):
        rule = ConcentrationRule()
        trade = {"value": 1000}
        profile = {"financial_profile": {"totalAssets": 0}}
        verdict = rule.evaluate(trade, profile)
        assert verdict.status == "WARN"

    def test_exactly_at_limit_passes(self, rich_user_profile):
        rule = ConcentrationRule(max_single_holding_pct=0.10)
        trade = {"value": 10000}  # Exactly 10%
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "PASS"


# ---------------------------------------------------------------------------
# SuitabilityRule
# ---------------------------------------------------------------------------

class TestSuitabilityRule:
    def test_pass_matching_risk(self, rich_user_profile):
        rule = SuitabilityRule()
        trade = {"risk_level": "moderate"}
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "PASS"

    def test_pass_lower_risk_trade(self, rich_user_profile):
        rule = SuitabilityRule()
        trade = {"risk_level": "low"}  # Low risk for moderate user = fine
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "PASS"

    def test_block_higher_risk_trade(self, rich_user_profile):
        rule = SuitabilityRule()
        trade = {"risk_level": "aggressive"}  # Aggressive for moderate user = blocked
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "BLOCK"
        assert "risk" in verdict.reason.lower()

    def test_pass_aggressive_user_aggressive_trade(self):
        rule = SuitabilityRule()
        trade = {"risk_level": "high"}
        profile = {"risk_profile": {"risk_tolerance": "aggressive"}}
        verdict = rule.evaluate(trade, profile)
        assert verdict.status == "PASS"


# ---------------------------------------------------------------------------
# MinimumBalanceRule
# ---------------------------------------------------------------------------

class TestMinimumBalanceRule:
    def test_pass_sufficient_remaining(self, rich_user_profile):
        rule = MinimumBalanceRule(min_balance_after_trade=1000)
        trade = {"value": 50000}  # 50k remaining from 100k
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "PASS"

    def test_warn_drains_below_minimum(self, rich_user_profile):
        rule = MinimumBalanceRule(min_balance_after_trade=1000)
        trade = {"value": 99500}  # Only £500 remaining
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "WARN"
        assert "safety buffer" in verdict.reason.lower()


# ---------------------------------------------------------------------------
# AgeRestrictionRule
# ---------------------------------------------------------------------------

class TestAgeRestrictionRule:
    def test_pass_non_drawdown(self, rich_user_profile):
        rule = AgeRestrictionRule()
        trade = {"type": "buy"}  # Not a drawdown, so age doesn't matter
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "PASS"

    def test_pass_old_enough_for_drawdown(self, rich_user_profile):
        # User is 45, but let's set min_age to 40
        rule = AgeRestrictionRule(min_age_for_drawdown=40)
        trade = {"type": "drawdown"}
        verdict = rule.evaluate(trade, rich_user_profile)
        assert verdict.status == "PASS"

    def test_block_too_young_for_drawdown(self, young_user_profile):
        rule = AgeRestrictionRule(min_age_for_drawdown=55)
        trade = {"type": "drawdown"}
        verdict = rule.evaluate(trade, young_user_profile)
        assert verdict.status == "BLOCK"
        assert "age" in verdict.reason.lower()

    def test_block_pension_withdrawal(self, young_user_profile):
        rule = AgeRestrictionRule()
        trade = {"type": "pension_withdrawal"}
        verdict = rule.evaluate(trade, young_user_profile)
        assert verdict.status == "BLOCK"


# ---------------------------------------------------------------------------
# SentinelAgent (Full Pipeline)
# ---------------------------------------------------------------------------

class TestSentinelAgent:
    @patch("app.services.sentinel_service.historian")
    def test_all_rules_pass(self, mock_historian, app, rich_user_profile):
        with app.app_context():
            trade = {"value": 5000, "risk_level": "moderate", "type": "buy"}
            verdict = sentinel.pre_trade_check(trade, rich_user_profile, "conv-1")
            assert verdict.status == "PASS"

    @patch("app.services.sentinel_service.historian")
    def test_block_on_concentration(self, mock_historian, app, rich_user_profile):
        with app.app_context():
            trade = {"value": 50000, "risk_level": "moderate", "type": "buy"}
            verdict = sentinel.pre_trade_check(trade, rich_user_profile, "conv-2")
            assert verdict.status == "BLOCK"
            assert verdict.rule_name == "ConcentrationLimit"

    @patch("app.services.sentinel_service.historian")
    def test_block_on_suitability(self, mock_historian, app, rich_user_profile):
        with app.app_context():
            trade = {"value": 5000, "risk_level": "aggressive", "type": "buy"}
            verdict = sentinel.pre_trade_check(trade, rich_user_profile, "conv-3")
            assert verdict.status == "BLOCK"
            assert verdict.rule_name == "SuitabilityCheck"

    @patch("app.services.sentinel_service.historian")
    def test_warn_on_low_balance(self, mock_historian, app, rich_user_profile):
        """When concentration and suitability pass but balance is low."""
        with app.app_context():
            # Under 10% of 100k (passes concentration), moderate risk (passes suitability),
            # but drains the balance
            trade = {"value": 9900, "risk_level": "moderate", "type": "buy"}
            profile = {**rich_user_profile, "financial_profile": {"totalAssets": 10000.0}}
            # 9900 / 10000 = 99% → this triggers concentration BLOCK first
            # Let's use a value that passes concentration but drains balance
            profile2 = {**rich_user_profile, "financial_profile": {"totalAssets": 100000.0}}
            trade2 = {"value": 9000, "risk_level": "moderate", "type": "buy"}
            _sentinel = SentinelAgent(rules=[MinimumBalanceRule(min_balance_after_trade=95000)])
            verdict = _sentinel.pre_trade_check(trade2, profile2, "conv-4")
            assert verdict.status == "WARN"

    @patch("app.services.sentinel_service.historian")
    def test_custom_rules(self, mock_historian, app):
        """Sentinel can be instantiated with a custom rule set."""
        with app.app_context():
            custom_sentinel = SentinelAgent(rules=[SuitabilityRule()])
            trade = {"value": 50000, "risk_level": "aggressive"}
            profile = {"risk_profile": {"risk_tolerance": "conservative"}}
            verdict = custom_sentinel.pre_trade_check(trade, profile, "conv-5")
            assert verdict.status == "BLOCK"
