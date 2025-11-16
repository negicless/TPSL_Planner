from __future__ import annotations
from typing import Optional, List
from tpsl_planner.core.auto_plan.base import (
    Strategy,
    StrategyPlan,
    PlanLeg,
    Target,
    Side
)
from tpsl_planner.core.levels import Level
from tpsl_planner.core.trend import TrendResult

class PullbackStrategy:
    name = "pullback"

    def build_plan(
        self,
        levels: List[Level],
        current_price: float,
        side_long: bool,
        trend: Optional[TrendResult] = None,
    ) -> Optional[StrategyPlan]:

        # ONLY LONG supported for now
        if not side_long:
            return None  

        # 1) Find first two supports below price  
        supports = [lv for lv in levels if lv.price < current_price][:3]
        if len(supports) < 1:
            return None

        # Basic 3-entry zone (refine later)
        top = supports[0].price
        bottom = supports[-1].price
        mid = (top + bottom) / 2

        entries = [
            PlanLeg(price=top, size_frac=0.3),
            PlanLeg(price=mid, size_frac=0.3),
            PlanLeg(price=bottom, size_frac=0.4),
        ]

        # 2) Stop = little below lowest support
        stop = bottom * 0.97  # placeholder until structure SL engine

        # 3) Targets (placeholder)
        targets = [
            Target(price=top * 1.05, label="TP1"),
            Target(price=top * 1.10, label="TP2"),
            Target(price=top * 1.15, label="TP3"),
        ]

        notes = "Basic pullback strategy. Improve later with structure detection."

        return StrategyPlan(
            name=self.name,
            side="LONG",
            entries=entries,
            stop=stop,
            targets=targets,
            notes=notes,
        )
