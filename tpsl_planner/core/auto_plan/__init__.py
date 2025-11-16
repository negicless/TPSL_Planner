from __future__ import annotations

from typing import List, Optional

from tpsl_planner.core.levels import Level
from tpsl_planner.core.trend import TrendResult

from .base import (
    StrategyPlan,
    AutoPlanResult,
    PlanLeg,
)
from .pullback import PullbackStrategy
from .breakout import BreakoutStrategy


# ----------------------------------------------------------
# Strategy registry (plugins)
# ----------------------------------------------------------

# Later you can add more:
# from .vwap import VWAPStrategy
# from .range import RangeStrategy
# etc.
STRATEGIES = [
    PullbackStrategy(),
    BreakoutStrategy(),
]


# ----------------------------------------------------------
# Helper: weighted average entry
# ----------------------------------------------------------

def _weighted_entry(entries: List[PlanLeg]) -> float:
    """
    Compute size-weighted average entry price from legs.
    If size fractions don't sum to 1, we normalize.
    """
    if not entries:
        raise ValueError("No entries in strategy plan.")

    total_weight = sum(leg.size_frac for leg in entries)
    if total_weight <= 0:
        # fallback: equal weight
        n = len(entries)
        return sum(leg.price for leg in entries) / n

    return sum(leg.price * leg.size_frac for leg in entries) / total_weight


# ----------------------------------------------------------
# New API: full auto-plan (multi-strategy)
# ----------------------------------------------------------

def compute_auto_plan_full(
    levels: List[Level],
    current_price: float,
    long_side: bool,
    trend: Optional[TrendResult] = None,
) -> AutoPlanResult:
    """
    Run all registered strategies and return an AutoPlanResult.

    - levels: structure levels (from your levels engine)
    - current_price: latest market price
    - long_side: True = long, False = short (short not yet implemented in strategies)
    - trend: optional TrendResult, if you want strategies to be trend-aware later
    """
    plans: List[StrategyPlan] = []

    for strat in STRATEGIES:
        try:
            plan = strat.build_plan(levels, current_price, long_side, trend)
        except Exception as e:
            # Don't let one broken strategy kill the whole planner.
            # You might log this in the future.
            plan = None

        if plan is not None:
            plans.append(plan)

    if not plans:
        raise ValueError("No valid strategy plan for this symbol/side.")

    # --------------------------------------------------
    # Primary plan selection logic
    # --------------------------------------------------
    # For now: just take the first plan in STRATEGIES that returns something.
    # Later:
    #   - prefer breakout if trend is strong
    #   - prefer pullback in weak/choppy market
    #   - choose plan with best R-multiple, etc.
    # --------------------------------------------------
    primary = plans[0]
    alternatives = plans[1:]

    return AutoPlanResult(
        primary=primary,
        alternatives=alternatives,
        trend=trend,
    )


# ----------------------------------------------------------
# Old API: simple (entry, sl, tp) triple for GUI
# ----------------------------------------------------------

def compute_auto_plan(
    levels: List[Level],
    current_price: float,
    long_side: bool,
) -> tuple[float, float, float]:
    """
    Backwards-compatible wrapper for the existing GUI.

    Returns:
        (entry, stop, target)

    It uses the 'primary' strategy plan from compute_auto_plan_full()
    and reduces it to a single average entry + first target.
    """
    # For now we don't pass trend in here; the GUI already computes trend separately.
    result = compute_auto_plan_full(
        levels=levels,
        current_price=current_price,
        long_side=long_side,
        trend=None,
    )

    plan = result.primary

    # Weighted average entry from all legs (E1/E2/E3)
    entry = _weighted_entry(plan.entries)

    stop = plan.stop

    if plan.targets:
        tp = plan.targets[0].price  # TP1 by default
    else:
        # Fallback: simple +5% target if strategy forgot targets
        tp = entry * 1.05

    return entry, stop, tp
