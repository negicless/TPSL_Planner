from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Optional, Protocol
from tpsl_planner.core.levels import Level
from tpsl_planner.core.trend import TrendResult

Side = Literal["LONG", "SHORT"]

@dataclass
class PlanLeg:
    price: float
    size_frac: float  # 0.3, 0.3, 0.4 etc.

@dataclass
class Target:
    price: float
    label: str        # "TP1", "TP2", ...

@dataclass
class StrategyPlan:
    name: str                 # "breakout", "pullback"
    side: Side
    entries: List[PlanLeg]
    stop: float
    targets: List[Target]
    notes: str = ""           # optional text (warnings etc.)

@dataclass
class AutoPlanResult:
    # so UI can still use a simple summary if it wants
    primary: StrategyPlan              # default / recommended
    alternatives: List[StrategyPlan]   # e.g. breakout + pullback
    trend: Optional[TrendResult] = None

class Strategy(Protocol):
    name: str

    def build_plan(
        self,
        levels: List[Level],
        current_price: float,
        side: bool,               # True=long, False=short  (for now)
        trend: Optional[TrendResult] = None,
    ) -> Optional[StrategyPlan]:
        ...
