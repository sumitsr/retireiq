import logging
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from app.services.audit_service import historian

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class SimulationResult:
    """
    Output of a Monte Carlo retirement simulation.

    success_rate:        Probability (0–1) of not outliving savings.
    median_final_value:  Median portfolio value at end of retirement.
    percentile_10:       10th percentile (pessimistic scenario).
    percentile_90:       90th percentile (optimistic scenario).
    simulations_run:     Number of simulations executed.
    yearly_percentiles:  Year-by-year 10th/50th/90th for charting.
    """
    success_rate: float
    median_final_value: float
    percentile_10: float
    percentile_90: float
    simulations_run: int
    yearly_percentiles: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# The Actuarial Agent
# ---------------------------------------------------------------------------

class ActuarialAgent:
    """
    Monte Carlo simulation engine for retirement planning.

    Answers the most critical question: "Will I actually have enough?"
    by running thousands of randomised scenarios through two lifecycle phases:

    1. Accumulation phase — saving toward retirement (contributions + returns)
    2. Decumulation phase — spending in retirement (withdrawals + returns)

    Each simulation samples annual returns from a normal distribution,
    naturally capturing the "sequence of returns" risk that deterministic
    calculators miss.
    """

    # --- Default assumptions (UK pension market, historical equity averages) ---
    DEFAULT_MEAN_RETURN = 0.07        # 7% average annual real return
    DEFAULT_STD_DEV = 0.15            # 15% annual volatility
    DEFAULT_INFLATION = 0.025         # 2.5% long-term inflation
    DEFAULT_SIMULATIONS = 10_000
    DECUMULATION_RETURN_HAIRCUT = 0.01  # Conservative shift in retirement

    def simulate(
        self,
        initial_portfolio: float,
        monthly_contribution: float,
        annual_withdrawal: float,
        current_age: int,
        retirement_age: int,
        life_expectancy: int = 90,
        mean_return: Optional[float] = None,
        std_dev: Optional[float] = None,
        inflation: Optional[float] = None,
        simulations: Optional[int] = None,
        conversation_id: Optional[str] = None,
    ) -> SimulationResult:
        """
        Runs the full Monte Carlo simulation and returns a SimulationResult
        with probability of success and percentile bands.
        """
        mean_return = mean_return or self.DEFAULT_MEAN_RETURN
        std_dev = std_dev or self.DEFAULT_STD_DEV
        inflation = inflation or self.DEFAULT_INFLATION
        simulations = simulations or self.DEFAULT_SIMULATIONS

        years_to_retirement = max(retirement_age - current_age, 0)
        years_in_retirement = max(life_expectancy - retirement_age, 0)
        total_years = years_to_retirement + years_in_retirement

        logger.info(
            "[Actuarial] Starting simulation | initial=£%.0f monthly=£%.0f "
            "withdrawal=£%.0f age=%d→%d→%d sims=%d conv=%s",
            initial_portfolio, monthly_contribution, annual_withdrawal,
            current_age, retirement_age, life_expectancy,
            simulations, conversation_id,
        )

        self._log_thought(
            conversation_id,
            f"Running {simulations:,} Monte Carlo scenarios: "
            f"age {current_age}→{retirement_age} (accumulation), "
            f"then {retirement_age}→{life_expectancy} (decumulation).",
        )

        # Run simulation
        success_count, all_trajectories = self._run_simulations(
            initial_portfolio, monthly_contribution, annual_withdrawal,
            years_to_retirement, years_in_retirement, total_years,
            mean_return, std_dev, inflation, simulations,
        )

        # Compute result
        result = self._compute_result(
            success_count, simulations, all_trajectories, total_years,
        )

        self._log_observation(
            conversation_id,
            f"Success rate: {result.success_rate:.1%}. "
            f"Median final: £{result.median_final_value:,.0f}. "
            f"Range: £{result.percentile_10:,.0f} – £{result.percentile_90:,.0f}.",
        )

        logger.info("[Actuarial] Simulation complete | success=%.1f%% conv=%s",
                    result.success_rate * 100, conversation_id)
        return result

    # -----------------------------------------------------------------------
    # Private — Core simulation engine
    # -----------------------------------------------------------------------

    def _run_simulations(
        self, initial, monthly, withdrawal, yrs_accum, yrs_decum,
        total_years, mean_ret, std, inflation, n_sims,
    ):
        """
        Runs n_sims independent portfolio trajectories.
        Returns (success_count, all_trajectories_matrix).
        """
        # Pre-allocate — shape: (n_sims, total_years + 1)
        trajectories = np.zeros((n_sims, total_years + 1))
        trajectories[:, 0] = initial
        success_count = 0

        # Vectorised return sampling for all sims × all years
        all_returns = np.random.normal(mean_ret, std, size=(n_sims, total_years))

        for sim in range(n_sims):
            portfolio = initial
            failed = False

            # Accumulation phase
            for yr in range(yrs_accum):
                r = all_returns[sim, yr]
                # Inflation-adjusted contribution
                real_contribution = monthly * 12 * ((1 + inflation) ** yr)
                portfolio = portfolio * (1 + r) + real_contribution
                trajectories[sim, yr + 1] = max(portfolio, 0)

            # Decumulation phase
            for yr in range(yrs_decum):
                total_yr = yrs_accum + yr
                r = all_returns[sim, total_yr] - self.DECUMULATION_RETURN_HAIRCUT
                # Inflation-adjusted withdrawal
                real_withdrawal = withdrawal * ((1 + inflation) ** total_yr)
                portfolio = portfolio * (1 + r) - real_withdrawal

                if portfolio <= 0:
                    portfolio = 0
                    failed = True
                    # Fill remaining years with zero
                    trajectories[sim, total_yr + 1:] = 0
                    break
                trajectories[sim, total_yr + 1] = portfolio

            if not failed:
                success_count += 1

        return success_count, trajectories

    def _compute_result(self, success_count, n_sims, trajectories, total_years):
        """Derives the SimulationResult from raw trajectory data."""
        final_values = trajectories[:, -1]

        # Year-by-year percentile bands for charting
        yearly_p10 = np.percentile(trajectories, 10, axis=0).tolist()
        yearly_p50 = np.percentile(trajectories, 50, axis=0).tolist()
        yearly_p90 = np.percentile(trajectories, 90, axis=0).tolist()

        return SimulationResult(
            success_rate=success_count / n_sims,
            median_final_value=float(np.median(final_values)),
            percentile_10=float(np.percentile(final_values, 10)),
            percentile_90=float(np.percentile(final_values, 90)),
            simulations_run=n_sims,
            yearly_percentiles={
                "p10": yearly_p10,
                "p50": yearly_p50,
                "p90": yearly_p90,
            },
        )

    # -----------------------------------------------------------------------
    # Private — Audit logging
    # -----------------------------------------------------------------------

    def _log_thought(self, conversation_id, content):
        historian.log_step(
            session_id=conversation_id,
            agent_name="Actuarial",
            step_type="THOUGHT",
            content=content,
        )

    def _log_observation(self, conversation_id, content):
        historian.log_step(
            session_id=conversation_id,
            agent_name="Actuarial",
            step_type="OBSERVATION",
            content=content,
        )

    # -----------------------------------------------------------------------
    # Public — Human-readable interpretation
    # -----------------------------------------------------------------------

    def format_summary(self, result: SimulationResult, retirement_age: int) -> str:
        """
        Converts the simulation result into a user-friendly summary string
        suitable for direct LLM response inclusion.
        """
        rate_pct = result.success_rate * 100

        if rate_pct >= 90:
            confidence = "very strong"
            advice = "Your current strategy looks excellent. Stay the course."
        elif rate_pct >= 75:
            confidence = "good"
            advice = "You're on a solid path, but consider small increases to your monthly contributions for extra security."
        elif rate_pct >= 50:
            confidence = "moderate"
            advice = "There's meaningful risk of a shortfall. Consider increasing contributions or adjusting your retirement age."
        else:
            confidence = "concerning"
            advice = "Your current trajectory has significant shortfall risk. A financial review is strongly recommended."

        return (
            f"**Retirement Simulation Results** ({result.simulations_run:,} scenarios)\n\n"
            f"- **Success Rate**: {rate_pct:.1f}% — your outlook is **{confidence}**.\n"
            f"- **Median Portfolio at Retirement**: £{result.median_final_value:,.0f}\n"
            f"- **Pessimistic (10th percentile)**: £{result.percentile_10:,.0f}\n"
            f"- **Optimistic (90th percentile)**: £{result.percentile_90:,.0f}\n\n"
            f"💡 *{advice}*"
        )


# Global singleton
actuarial = ActuarialAgent()
