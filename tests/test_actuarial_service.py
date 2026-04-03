"""
Tests for the Actuarial Agent (Monte Carlo Retirement Simulation).
"""
import pytest
from unittest.mock import patch
from app.services.actuarial_service import actuarial, ActuarialAgent, SimulationResult


# ---------------------------------------------------------------------------
# SimulationResult
# ---------------------------------------------------------------------------

class TestSimulationResult:
    def test_dataclass_fields(self):
        result = SimulationResult(
            success_rate=0.78,
            median_final_value=250000.0,
            percentile_10=50000.0,
            percentile_90=600000.0,
            simulations_run=1000,
        )
        assert result.success_rate == 0.78
        assert result.median_final_value == 250000.0
        assert result.simulations_run == 1000
        assert result.yearly_percentiles == {}


# ---------------------------------------------------------------------------
# ActuarialAgent.simulate
# ---------------------------------------------------------------------------

class TestActuarialSimulate:
    @patch("app.services.actuarial_service.historian")
    def test_basic_simulation_returns_result(self, mock_historian, app):
        """Simulation runs and returns a valid SimulationResult."""
        with app.app_context():
            result = actuarial.simulate(
                initial_portfolio=100000,
                monthly_contribution=500,
                annual_withdrawal=30000,
                current_age=35,
                retirement_age=65,
                life_expectancy=90,
                simulations=100,  # Small for test speed
                conversation_id="test-conv",
            )
            assert isinstance(result, SimulationResult)
            assert 0.0 <= result.success_rate <= 1.0
            assert result.simulations_run == 100
            assert result.median_final_value >= 0

    @patch("app.services.actuarial_service.historian")
    def test_success_rate_range(self, mock_historian, app):
        """Success rate must always be between 0 and 1."""
        with app.app_context():
            result = actuarial.simulate(
                initial_portfolio=500000,
                monthly_contribution=2000,
                annual_withdrawal=20000,
                current_age=50,
                retirement_age=65,
                life_expectancy=85,
                simulations=200,
            )
            assert 0.0 <= result.success_rate <= 1.0

    @patch("app.services.actuarial_service.historian")
    def test_large_savings_high_success(self, mock_historian, app):
        """Very large portfolio + small withdrawal → high success rate."""
        with app.app_context():
            result = actuarial.simulate(
                initial_portfolio=10_000_000,   # 10M
                monthly_contribution=5000,
                annual_withdrawal=20000,        # Only 20k/year
                current_age=60,
                retirement_age=65,
                life_expectancy=85,
                simulations=200,
            )
            assert result.success_rate > 0.90

    @patch("app.services.actuarial_service.historian")
    def test_zero_savings_low_success(self, mock_historian, app):
        """Zero savings + large withdrawal → very low success rate."""
        with app.app_context():
            result = actuarial.simulate(
                initial_portfolio=1000,       # Near-zero
                monthly_contribution=0,
                annual_withdrawal=50000,      # Huge withdrawal
                current_age=60,
                retirement_age=65,
                life_expectancy=90,
                simulations=200,
            )
            assert result.success_rate < 0.30

    @patch("app.services.actuarial_service.historian")
    def test_already_retired(self, mock_historian, app):
        """current_age >= retirement_age → no accumulation phase."""
        with app.app_context():
            result = actuarial.simulate(
                initial_portfolio=500000,
                monthly_contribution=0,
                annual_withdrawal=30000,
                current_age=67,
                retirement_age=65,  # Already past retirement
                life_expectancy=90,
                simulations=100,
            )
            assert isinstance(result, SimulationResult)
            assert result.simulations_run == 100

    @patch("app.services.actuarial_service.historian")
    def test_percentile_ordering(self, mock_historian, app):
        """p10 <= median <= p90 must always hold."""
        with app.app_context():
            result = actuarial.simulate(
                initial_portfolio=200000,
                monthly_contribution=1000,
                annual_withdrawal=25000,
                current_age=40,
                retirement_age=65,
                life_expectancy=90,
                simulations=500,
            )
            assert result.percentile_10 <= result.median_final_value
            assert result.median_final_value <= result.percentile_90

    @patch("app.services.actuarial_service.historian")
    def test_yearly_percentiles_populated(self, mock_historian, app):
        """Yearly percentile bands must be present and correctly sized."""
        with app.app_context():
            result = actuarial.simulate(
                initial_portfolio=100000,
                monthly_contribution=500,
                annual_withdrawal=25000,
                current_age=50,
                retirement_age=65,
                life_expectancy=85,
                simulations=100,
            )
            total_years = (65 - 50) + (85 - 65)  # 15 + 20 = 35
            assert "p10" in result.yearly_percentiles
            assert "p50" in result.yearly_percentiles
            assert "p90" in result.yearly_percentiles
            # Length should be total_years + 1 (including year 0)
            assert len(result.yearly_percentiles["p50"]) == total_years + 1

    @patch("app.services.actuarial_service.historian")
    def test_historian_is_called(self, mock_historian, app):
        """Verify the Historian audit trail is populated."""
        with app.app_context():
            actuarial.simulate(
                initial_portfolio=100000,
                monthly_contribution=500,
                annual_withdrawal=25000,
                current_age=40,
                retirement_age=65,
                simulations=50,
                conversation_id="audit-test",
            )
            # Should have at least 2 calls: THOUGHT + OBSERVATION
            assert mock_historian.log_step.call_count >= 2

            # Verify the first call is a THOUGHT
            first_call = mock_historian.log_step.call_args_list[0]
            assert first_call.kwargs.get("step_type") == "THOUGHT" or \
                   (len(first_call.args) > 0 and "THOUGHT" in str(first_call))


# ---------------------------------------------------------------------------
# ActuarialAgent.format_summary
# ---------------------------------------------------------------------------

class TestFormatSummary:
    def test_very_strong_outlook(self):
        result = SimulationResult(
            success_rate=0.95, median_final_value=500000,
            percentile_10=200000, percentile_90=900000, simulations_run=10000,
        )
        summary = actuarial.format_summary(result, retirement_age=65)
        assert "very strong" in summary.lower()
        assert "95.0%" in summary

    def test_good_outlook(self):
        result = SimulationResult(
            success_rate=0.80, median_final_value=300000,
            percentile_10=100000, percentile_90=600000, simulations_run=10000,
        )
        summary = actuarial.format_summary(result, retirement_age=67)
        assert "good" in summary.lower()

    def test_moderate_outlook(self):
        result = SimulationResult(
            success_rate=0.55, median_final_value=100000,
            percentile_10=0, percentile_90=300000, simulations_run=10000,
        )
        summary = actuarial.format_summary(result, retirement_age=65)
        assert "moderate" in summary.lower()

    def test_concerning_outlook(self):
        result = SimulationResult(
            success_rate=0.30, median_final_value=20000,
            percentile_10=0, percentile_90=100000, simulations_run=10000,
        )
        summary = actuarial.format_summary(result, retirement_age=67)
        assert "concerning" in summary.lower()
        assert "financial review" in summary.lower()

    def test_summary_contains_key_metrics(self):
        result = SimulationResult(
            success_rate=0.78, median_final_value=250000,
            percentile_10=50000, percentile_90=600000, simulations_run=10000,
        )
        summary = actuarial.format_summary(result, retirement_age=65)
        assert "78.0%" in summary
        assert "10,000" in summary  # simulations_run formatted
        assert "250,000" in summary  # median
