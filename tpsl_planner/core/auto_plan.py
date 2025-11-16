# tpsl_planner/core/auto_plan.py
   # - compute_recommended_plan(levels, curr_price, side) -> (entry, sl, tp)


# tpsl_planner/core/auto_plan.py
from __future__ import annotations

from typing import List, Optional, Tuple

from tpsl_planner.core.levels import Level


def _tf_priority(tf: str) -> int:
    """
    Priority for choosing structural SL/TP.
    Higher = more important (W > D > 4H > 1H > 30m).
    """
    tfu = (tf or "").upper()
    if tfu.startswith("W-LOW"):
        return 100
    if tfu.startswith("W-1"):
        return 95
    if tfu.startswith("W"):
        return 90
    if tfu.startswith("D"):
        return 80
    if "4H" in tfu:
        return 70
    if "1H" in tfu:
        return 60
    if "30" in tfu:
        return 50
    return 10


def compute_auto_plan(
    levels: List[Level],
    current_price: float,
    long_side: bool = True,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Given a list of Level objects and current price, propose (entry, sl, tp).

    LONG:
      - Entry: closest support <= current_price
      - SL   : strongest HTF support (highest tf priority, then lowest price)
      - TP   : closest resistance >= entry (or >= current_price if entry None)

    SHORT:
      - Entry: closest resistance >= current_price
      - SL   : strongest HTF resistance (highest tf priority, then highest price)
      - TP   : closest support <= entry (or <= current_price if entry None)
    """
    if not levels:
        return None, None, None

    supports = [lv for lv in levels if lv.kind == "support"]
    resists  = [lv for lv in levels if lv.kind == "resistance"]

    if long_side:
        # ---------- LONG ENTRY ----------
        below = [lv for lv in supports if lv.price <= current_price]
        if below:
            entry = max(below, key=lambda lv: lv.price).price
        else:
            # fallback: nearest support by absolute distance
            entry = min(supports, key=lambda lv: abs(lv.price - current_price)).price if supports else None

        # ---------- LONG SL ----------
        sl = None
        if supports:
            # sort by (priority desc, price asc) → HTF & deeper
            best_sl = min(
                supports,
                key=lambda lv: (-_tf_priority(lv.timeframe), lv.price),
            )
            sl = best_sl.price

        # ---------- LONG TP ----------
        base = entry if entry is not None else current_price
        above = [lv for lv in resists if lv.price >= base]
        if above:
            tp = min(above, key=lambda lv: lv.price).price
        else:
            tp = max(resists, key=lambda lv: lv.price).price if resists else None

        return entry, sl, tp

    # ================= SHORT SIDE =================

    # ---------- SHORT ENTRY ----------
    above_r = [lv for lv in resists if lv.price >= current_price]
    if above_r:
        entry = min(above_r, key=lambda lv: lv.price).price
    else:
        entry = min(resists, key=lambda lv: abs(lv.price - current_price)).price if resists else None

    # ---------- SHORT SL ----------
    sl = None
    if resists:
        # sort by (priority desc, price desc) → HTF & higher
        best_sl = max(
            resists,
            key=lambda lv: (_tf_priority(lv.timeframe), lv.price),
        )
        sl = best_sl.price

    # ---------- SHORT TP ----------
    base = entry if entry is not None else current_price
    below_s = [lv for lv in supports if lv.price <= base]
    if below_s:
        tp = max(below_s, key=lambda lv: lv.price).price
    else:
        tp = min(supports, key=lambda lv: lv.price).price if supports else None

    return entry, sl, tp
