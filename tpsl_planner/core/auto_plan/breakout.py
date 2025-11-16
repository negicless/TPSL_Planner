from __future__ import annotations
from typing import Optional, List

from tpsl_planner.core.auto_plan.base import (
    Strategy,
    StrategyPlan,
    PlanLeg,
    Target
)
from tpsl_planner.core.levels import Level
from tpsl_planner.core.trend import TrendResult

class BreakoutStrategy:
    name = "breakout"

    def build_plan(
        self,
        levels: List[Level],
        current_price: float,
        side_long: bool,
        trend: Optional[TrendResult] = None,
    ) -> Optional[StrategyPlan]:

        if not side_long:
            return None

        # 1) Find nearest resistance above price
        resistances = [lv for lv in levels if lv.price > current_price]
        if not resistances:
            return None

        trigger = resistances[0].price

        # 2) SL = below trigger (placeholder logic)
        stop = trigger * 0.96  

        # 3) Targets (extension levels)
        targets = [
            Target(price=trigger * 1.05, label="TP1"),
            Target(price=trigger * 1.10, label="TP2"),
            Target(price=trigger * 1.15, label="TP3"),
            Target(price=trigger * 1.20, label="TP4"),
        ]

        # Entries: single breakout entry for now
        entries = [
            PlanLeg(price=trigger, size_frac=1.0),
        ]

        notes = "Basic breakout strategy. Trigger above first resistance."

        return StrategyPlan(
            name=self.name,
            side="LONG",
            entries=entries,
            stop=stop,
            targets=targets,
            notes=notes,
        )
