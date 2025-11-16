from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd


@dataclass
class TrendConfig:
    ema_fast: int = 8
    ema_mid: int = 21
    ema_slow: int = 50

    # structure
    weight_stack: float = 40.0   # EMA stacking
    weight_slope: float = 30.0   # slope of slow EMA

    # new: momentum + ADX weights
    weight_momentum: float = 20.0
    weight_adx: float = 10.0

    slope_lookback: int = 10

    # volatility (unchanged)
    vol_lookback: int = 20
    vol_high_z: float = 1.0
    vol_low_z: float = -0.5

    # normalization params
    # 1% move of EMA_slow over slope_lookback -> full slope_score
    slope_full_move: float = 0.01
    # MACD |hist| around this or higher -> full MACD contribution
    macd_full: float = 2.0
    # ADX thresholds
    adx_min_trend: float = 10.0
    adx_full_trend: float = 35.0


@dataclass
class TrendResult:
    score: float                # 0–100 (overall trend quality)
    direction: str              # "UP" / "DOWN" / "CHOP"
    label: str                  # human label (compatible with your old code)
    vol_state: str              # "LOW" / "NORMAL" / "HIGH"

    # --- new fields ---
    trend_type: str             # "Stable Up" / "Unstable Up" / "Chop" / "Down"
    momentum_score: float       # 0–100
    momentum_label: str         # "Weak" / "Medium" / "Strong"

    components: Dict[str, float]
    raw: Dict[str, Any]


def _ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _momentum_from_rsi_macd(
    rsi: Optional[float],
    macd_hist: Optional[float],
    cfg: TrendConfig,
) -> float:
    """
    Return 0–1 momentum score using RSI + MACD hist.
    If inputs are missing, returns 0.0.
    """
    if rsi is None and macd_hist is None:
        return 0.0

    rsi_score = 0.0
    macd_score = 0.0

    if rsi is not None:
        # distance from neutral 50; 10–90 mapped to 0..1
        rsi_dev = abs(rsi - 50.0) / 40.0
        rsi_score = _clip(rsi_dev, 0.0, 1.0)

    if macd_hist is not None:
        macd_norm = abs(macd_hist) / cfg.macd_full
        macd_score = _clip(macd_norm, 0.0, 1.0)

    # if both present: MACD a bit more important
    if rsi is not None and macd_hist is not None:
        return _clip(0.6 * macd_score + 0.4 * rsi_score, 0.0, 1.0)
    # only one present
    return _clip(max(rsi_score, macd_score), 0.0, 1.0)


def _momentum_label(score_0_1: float) -> str:
    if score_0_1 < 0.33:
        return "Weak"
    elif score_0_1 < 0.66:
        return "Medium"
    return "Strong"


def _adx_score(adx: Optional[float], cfg: TrendConfig) -> float:
    """
    Map ADX -> 0..1. If missing, returns 0.
    """
    if adx is None:
        return 0.0

    if adx <= cfg.adx_min_trend:
        return 0.0
    if adx >= cfg.adx_full_trend:
        return 1.0
    return _clip(
        (adx - cfg.adx_min_trend) / (cfg.adx_full_trend - cfg.adx_min_trend),
        0.0,
        1.0,
    )


def format_ema_stack(ema_fast: float, ema_mid: float, ema_slow: float) -> str:
    """Return a clean stack string: EMA8(x) < EMA21(y) < EMA50(z) etc."""
    f = f"{ema_fast:.2f}"
    m = f"{ema_mid:.2f}"
    s = f"{ema_slow:.2f}"

    if ema_fast < ema_mid < ema_slow:
        return f"EMA8({f}) < EMA21({m}) < EMA50({s})"
    elif ema_fast > ema_mid > ema_slow:
        return f"EMA8({f}) > EMA21({m}) > EMA50({s})"
    else:
        return f"EMA8({f}), EMA21({m}), EMA50({s}) (mixed)"


def compute_trend(df: pd.DataFrame, config: TrendConfig | None = None) -> TrendResult:
    """
    EMA + momentum + ADX based trend engine.

    df: DataFrame with columns:
        'close' (required)
        optional: 'rsi', 'macd_hist', 'adx', 'volume'
    """
    if config is None:
        config = TrendConfig()

    if "close" not in df.columns:
        raise ValueError("DataFrame must have a 'close' column")

    # --- make sure `close` is a 1-D Series, not a DataFrame ---
    close_raw = df["close"]
    if isinstance(close_raw, pd.DataFrame):
        # e.g. MultiIndex or duplicate column names → take the first column
        close = close_raw.iloc[:, 0].astype(float)
    else:
        # ensure it's a Series and cast to float
        close = pd.Series(close_raw, copy=False).astype(float)

    if len(close) < config.ema_slow + config.slope_lookback + 5:
        raise ValueError("Not enough data for trend computation")

    ema_fast = _ema(close, config.ema_fast)
    ema_mid = _ema(close, config.ema_mid)
    ema_slow = _ema(close, config.ema_slow)

    # ----- last values -----
    c  = float(close.iloc[-1])
    ef = float(ema_fast.iloc[-1])
    em = float(ema_mid.iloc[-1])
    es = float(ema_slow.iloc[-1])

    # ... keep the rest of your function exactly the same ...


    # optional signals
    rsi_val: Optional[float] = float(df["rsi"].iloc[-1]) if "rsi" in df.columns else None
    macd_val: Optional[float] = float(df["macd_hist"].iloc[-1]) if "macd_hist" in df.columns else None
    adx_val: Optional[float] = float(df["adx"].iloc[-1]) if "adx" in df.columns else None

    # =====================================================
    # 1) EMA stacking score (structure)
    # =====================================================
    if ef > em > es:
        stack_score = config.weight_stack          # strong uptrend
        direction = "UP"
    elif ef < em < es:
        stack_score = config.weight_stack          # strong downtrend
        direction = "DOWN"
    else:
        stack_score = config.weight_stack * 0.4    # messy stack
        direction = "CHOP"

    # =====================================================
    # 2) EMA slow slope score (trend persistence)
    # =====================================================
    slow = ema_slow
    n = config.slope_lookback
    # slope = (EMA_slow[t] - EMA_slow[t-n]) / (n * price)
    slope = (slow.iloc[-1] - slow.iloc[-1 - n]) / (n * c)
    # normalize slope into 0–1 by clipping
    slope_norm = _clip(
        abs(slope) / config.slope_full_move,
        0.0,
        1.0,
    )  # full_score if move >= slope_full_move over n bars
    slope_score = config.weight_slope * slope_norm

    # refine direction using slope sign
    if slope > 0 and direction != "DOWN":
        direction = "UP"
    elif slope < 0 and direction != "UP":
        direction = "DOWN"
    else:
        direction = "CHOP"

    # =====================================================
    # 3) Momentum (RSI + MACD)
    # =====================================================
    mom_0_1 = _momentum_from_rsi_macd(rsi_val, macd_val, config)
    momentum_score = mom_0_1 * 100.0

    # effective weight: if we don't have any momentum inputs, we drop this weight
    momentum_weight = config.weight_momentum if (rsi_val is not None or macd_val is not None) else 0.0
    momentum_contrib = momentum_weight * mom_0_1

    # =====================================================
    # 4) ADX (trend strength)
    # =====================================================
    adx_0_1 = _adx_score(adx_val, config)
    adx_score = adx_0_1 * 100.0
    adx_weight = config.weight_adx if adx_val is not None else 0.0
    adx_contrib = adx_weight * adx_0_1

    # =====================================================
    # 5) Combine into final score (0–100)
    # =====================================================
    total_raw = stack_score + slope_score + momentum_contrib + adx_contrib
    total_weight = config.weight_stack + config.weight_slope + momentum_weight + adx_weight
    total_weight = total_weight or 1.0  # avoid div by zero

    score = 100.0 * total_raw / total_weight
    score = float(_clip(score, 0.0, 100.0))

    # =====================================================
    # 6) Label (keep your style but now based on total score)
    # =====================================================
    if score >= 80:
        label = "Strong Uptrend" if direction == "UP" else "Strong Downtrend"
    elif score >= 65:
        label = "Stable Uptrend" if direction == "UP" else "Weak Downtrend"
    elif score >= 50:
        label = "Range / Mixed"
    elif score >= 35:
        label = "Weak Downtrend" if direction == "DOWN" else "Weak Uptrend"
    else:
        label = "No Clear Trend"

    # =====================================================
    # 7) Volatility state (same logic as before)
    # =====================================================
    ret = close.pct_change().dropna()
    recent = ret.tail(config.vol_lookback)
    mean_vol = float(recent.std(ddof=0))  # std of returns

    if len(recent) > 1:
        latest_block = ret.tail(5).std(ddof=0)
    else:
        latest_block = mean_vol
    std_vol = mean_vol or 1e-9
    z = (latest_block - mean_vol) / std_vol

    if z >= config.vol_high_z:
        vol_state = "HIGH"
    elif z <= config.vol_low_z:
        vol_state = "LOW"
    else:
        vol_state = "NORMAL"

    # =====================================================
    # 8) Trend type + momentum label (for ADA-style output)
    # =====================================================
    mom_label = _momentum_label(mom_0_1)

    # Stable / Unstable / Chop – direction aware
    if direction == "UP":
        if score >= 75 and adx_0_1 >= 0.5:
            trend_type = "Stable Up"
        elif score >= 60:
            trend_type = "Unstable Up"
        else:
            trend_type = "Chop"
    elif direction == "DOWN":
        if score >= 75 and adx_0_1 >= 0.5:
            trend_type = "Stable Down"
        elif score >= 60:
            trend_type = "Unstable Down"
        else:
            trend_type = "Chop"
    else:
        trend_type = "Chop"


    ema_stack_text = format_ema_stack(ef, em, es)

    components = {
        "ema_stack": stack_score / (config.weight_stack or 1.0) * 100.0,
        "ema_slope": slope_score / (config.weight_slope or 1.0) * 100.0,
        "momentum": (momentum_contrib / (momentum_weight or 1.0) * 100.0) if momentum_weight > 0 else 0.0,
        "adx": (adx_contrib / (adx_weight or 1.0) * 100.0) if adx_weight > 0 else 0.0,
    }

    raw = {
        "close": c,
        "ema_fast": ef,
        "ema_mid": em,
        "ema_slow": es,
        "ema_stack": ema_stack_text,
        "slope": slope,
        "slope_norm": slope_norm,
        "rsi": rsi_val,
        "macd_hist": macd_val,
        "adx": adx_val,
        "momentum_0_1": mom_0_1,
        "adx_0_1": adx_0_1,
        "vol_z": z,
    }

    return TrendResult(
        score=score,
        direction=direction,
        label=label,
        vol_state=vol_state,
        trend_type=trend_type,
        momentum_score=momentum_score,
        momentum_label=mom_label,
        components=components,
        raw=raw,
    )


def trend_comment(res: TrendResult) -> str:
    """
    Human-readable comment.
    First line = EMA stack.
    Second line = trend summary (same style as Auto Plan dialog).
    """
    stack = res.raw.get("ema_stack", "")

    base = (
        f"Trend: {res.label}  "
        f"(score {res.score:.0f}, dir {res.direction}, "
        f"Momentum={res.momentum_label}, Vol={res.vol_state})"
    )

    if stack:
        return f"{stack}\n{base}"
    return base

