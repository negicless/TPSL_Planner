# tpsl_engine.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Literal, Dict

Side = Literal["long", "short"]

# ---------- Data models ----------
@dataclass
class VolMetrics:
    atr: float            # e.g. ATR(14) in price units
    atr_pct: float        # ATR / close (0.034 = 3.4%)
    rvol: float           # RVOL (today / 20d avg), optional but recommended

@dataclass
class LevelSet:
    support: List[float]
    resistance: List[float]

@dataclass
class Levels:
    h4: LevelSet
    d: LevelSet
    w: LevelSet

@dataclass
class MarketConfig:
    # Provide simple defaults; override with your JP/US tick+lot funcs
    tick_size: float = 1.0
    lot_size: int = 1

    # Optional hooks if you want dynamic ladders
    def get_tick(self, price: float) -> float:
        return self.tick_size

    def get_lot(self, price: float) -> int:
        return self.lot_size

@dataclass
class PlanResult:
    ok: bool
    reason: Optional[str] = None
    regime: Optional[str] = None
    entry: Optional[float] = None
    stop: Optional[float] = None
    t1: Optional[float] = None
    t2: Optional[float] = None
    r1: Optional[float] = None
    r2: Optional[float] = None
    shares: Optional[int] = None
    risk_amount: Optional[float] = None
    scale_plan: Optional[List[Dict]] = None
    notes: Optional[List[str]] = None

# ---------- Core helpers ----------
def _nearest_below(x: float, arr: List[float]) -> Optional[float]:
    cand = [a for a in arr if a < x]
    return max(cand) if cand else None

def _nearest_above(x: float, arr: List[float]) -> Optional[float]:
    cand = [a for a in arr if a > x]
    return min(cand) if cand else None

def _round_to_tick(price: float, tick: float, *, up: bool) -> float:
    if tick <= 0:
        return price
    k = int(price / tick)
    rounded = k * tick
    if up and rounded < price - 1e-12:
        rounded += tick
    if (not up) and rounded > price + 1e-12:
        rounded -= tick
    # avoid tiny FP noise
    return float(round(rounded / tick) * tick)

def classify_regime(atr_pct: float, rvol: float) -> str:
    # Tunable thresholds
    if atr_pct > 0.07 or rvol > 2.5: return "wild"
    if atr_pct > 0.04 or rvol > 1.5: return "hot"
    if atr_pct > 0.02 or rvol > 0.8:  return "normal"
    return "calm"

# ---------- Public API ----------
def plan_dynamic_tpsl(
    entry: float,
    side: Side,
    vol: VolMetrics,
    levels: Levels,
    *,
    account_equity: float = 2_000_000.0,
    risk_pct: float = 0.01,
    mkt: MarketConfig = MarketConfig(),
    regime: Optional[str] = None,
) -> PlanResult:
    """
    Volatility- & structure-aware TPSL planner.
    Pure function: no UI, no I/O.
    """
    if entry <= 0 or vol.atr <= 0:
        return PlanResult(ok=False, reason="Invalid entry or ATR.")

    regime = regime or classify_regime(vol.atr_pct, vol.rvol)

    k_buf = {"calm":0.5, "normal":0.8, "hot":1.0, "wild":1.3}[regime]
    m1, m2 = {
        "calm": (0.8, 1.5),
        "normal": (1.0, 2.0),
        "hot": (1.3, 2.6),
        "wild": (1.8, 3.2),
    }[regime]

    sup_all = levels.h4.support + levels.d.support + levels.w.support
    res_all = levels.h4.resistance + levels.d.resistance + levels.w.resistance

    if side == "long":
        base = _nearest_below(entry, sup_all)
        stop_raw = (base if base is not None else entry - vol.atr) - k_buf * vol.atr
        t1_struct = _nearest_above(entry, res_all)
        t2_struct = _nearest_above(t1_struct if t1_struct else entry + 9e9, res_all)
        t1_raw = min(t1_struct if t1_struct else entry + 9e9, entry + m1 * vol.atr)
        t2_raw = min(t2_struct if t2_struct else entry + 9e9, entry + m2 * vol.atr)
        stop_upflag = False
        t_upflag = True
    else:
        base = _nearest_above(entry, res_all)
        stop_raw = (base if base is not None else entry + vol.atr) + k_buf * vol.atr
        t1_struct = _nearest_below(entry, sup_all)
        t2_struct = _nearest_below(t1_struct if t1_struct else entry - 9e9, sup_all)
        t1_raw = max(t1_struct if t1_struct else entry - 9e9, entry - m1 * vol.atr)
        t2_raw = max(t2_struct if t2_struct else entry - 9e9, entry - m2 * vol.atr)
        stop_upflag = True
        t_upflag = False

    tick = mkt.get_tick(entry)
    lot  = mkt.get_lot(entry)

    stop = _round_to_tick(stop_raw, tick, up=stop_upflag)
    t1   = _round_to_tick(t1_raw,   tick, up=t_upflag)
    t2   = _round_to_tick(t2_raw,   tick, up=t_upflag)

    stop_dist = abs(entry - stop)
    if stop_dist <= 0:
        return PlanResult(ok=False, reason="Zero/negative stop distance.")

    risk_amount = account_equity * max(0.0, risk_pct)
    raw_shares = int(risk_amount // (stop_dist * max(1, lot)))
    shares = max(0, raw_shares - (raw_shares % max(1, lot)))

    if shares == 0:
        return PlanResult(ok=False, reason="Position too small at given risk/stop.")

    r1 = abs(t1 - entry) / stop_dist
    r2 = abs(t2 - entry) / stop_dist
    if r1 < 1.7:
        return PlanResult(ok=False, reason=f"RR too low to T1 ({r1:.2f}R). Wait for better entry.")

    if regime in ("hot", "wild"):
        scale = [
            {"qty": int(shares * 0.40), "take": t1},
            {"qty": int(shares * 0.40), "take": t2},
            {"qty": shares - int(shares * 0.80), "take": None, "trail": "4H_swing - 0.8*ATR"},
        ]
    else:
        scale = [
            {"qty": int(shares * 0.50), "take": t1},
            {"qty": shares - int(shares * 0.50), "take": t2},
        ]

    return PlanResult(
        ok=True,
        regime=regime,
        entry=entry,
        stop=stop,
        t1=t1,
        t2=t2,
        r1=round(r1, 2),
        r2=round(r2, 2),
        shares=shares,
        risk_amount=risk_amount,
        scale_plan=scale,
        notes=[
            "Move stop to breakeven after a close beyond T1 on your decision timeframe.",
            "Then step-trail at last 4H swing with regime buffer.",
        ],
    )

# ---------- Convenience formatting ----------
def fmt2(x: Optional[float]) -> str:
    return "" if x is None else f"{x:.2f}"
