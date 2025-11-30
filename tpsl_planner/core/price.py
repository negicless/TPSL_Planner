# tpsl_app/price.py
from __future__ import annotations

import time
import re
from dataclasses import dataclass
from typing import Optional

try:
    import yfinance as yf
except Exception:
    yf = None  # we'll error nicely if missing

try:
    import pandas as pd
except Exception:
    pd = None  # only needed for OHLC history


@dataclass(slots=True)
class PriceResult:
    symbol: str
    price: float
    asof: float  # unix timestamp


class PriceError(Exception):
    pass


# --- tiny in-memory cache for last price (avoid hammering on repeated clicks) ---
_TTL = 15  # seconds
_CACHE: dict[str, PriceResult] = {}


# ---------------- symbol helpers ----------------

def normalize_symbol(raw: str) -> str:
    """
    Normalize user-facing symbol to something yfinance understands.

    - Strips JP-/US- prefixes
    - JP numeric codes (4 digits) => append .T
    """
    s = (raw or "").strip().upper()
    if not s:
        return ""
    if s.startswith("US-"):
        s = s[3:]
    elif s.startswith("JP-"):
        s = s[3:]
    # Only append .T for exactly 4 digits
    if re.fullmatch(r"\d{4}", s):
        return s + ".T"
    return s


def _is_jpx(symbol: str) -> bool:
    return symbol.endswith(".T")


def _should_use_prepost(symbol: str) -> bool:
    """
    Use pre/post sessions for non-JPX equities (e.g., US).
    JPX doesn't have pre/post on Yahoo, so keep it False there.
    """
    return not _is_jpx(symbol)


# ---------------- intraday last price fetcher ----------------

def _fetch_yfinance(symbol: str) -> float | None:
    """
    Return the most recent available price.

    For US/most non-JPX: include pre/post by using intraday (1m) with prepost=True.
    For JPX (.T): fetch intraday (1m) regular hours only (Yahoo JP has no pre/post).
    """
    if not yf:
        raise PriceError("yfinance is not installed. Run: pip install yfinance")

    try:
        # 1) Try fast path if it already includes a sane last price
        t = yf.Ticker(symbol)
        fi = getattr(t, "fast_info", None)
        if fi:
            # yfinance>=0.2 exposes fast_info.last_price (best-effort latest)
            lp = getattr(fi, "last_price", None)
            if lp is not None and float(lp) > 0:
                return float(lp)

        # 2) Robust path: intraday with/without pre/post depending on exchange
        prepost = _should_use_prepost(symbol)

        # First try 1 trading day to keep it light.
        df = yf.download(
            symbol, period="1d", interval="1m", prepost=prepost, progress=False
        )
        if df is None or df.empty:
            # Fallback to 5d in case of holiday/weekend or late sessions
            df = yf.download(
                symbol, period="5d", interval="1m", prepost=prepost, progress=False
            )

        if df is not None and not df.empty:
            # The last close value is the most recent tick we have (pre/post included if requested)
            return float(df["Close"].iloc[-1])

        return None

    except Exception as e:
        raise PriceError(f"yfinance fetch failed for {symbol}: {e}") from e


# ---------------- OHLCV history for levels / charts ----------------

def load_ohlc_for_levels(
    raw_symbol: str,
    *,
    period: str = "60d",
    interval: str = "30m",
    prepost: Optional[bool] = None,
):
    """
    Load OHLCV history suitable for mentor-style levels engine.

    - Uses the same normalize_symbol() rules as get_last_price
    - Defaults to 60 days of 30m bars (good for resampling to W/D/4H/30m)
    - For JPX (.T): pre/post is forced to False
    - For non-JPX: pre/post defaults to True unless overridden

    Returns
    -------
    pandas.DataFrame with columns:
        open, high, low, close, volume
    and DatetimeIndex.
    """
    if not yf:
        raise PriceError("yfinance is not installed. Run: pip install yfinance")
    if pd is None:
        raise PriceError("pandas is required for OHLC history. Run: pip install pandas")

    symbol = normalize_symbol(raw_symbol)
    if not symbol:
        raise PriceError("Empty ticker for OHLC loader.")

    # Decide pre/post behavior if not explicitly given
    if prepost is None:
        prepost = _should_use_prepost(symbol)

    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            prepost=prepost,
            auto_adjust=False,
            progress=False,
        )
    except Exception as e:
        raise PriceError(f"yfinance OHLC fetch failed for {symbol}: {e}") from e

    if df is None or df.empty:
        raise PriceError(f"No OHLC data returned for {symbol} (period={period}, interval={interval})")

    # Normalize columns to what our levels engine expects
    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )

    # Ensure we at least have open/high/low/close
    for col in ("open", "high", "low", "close"):
        if col not in df.columns:
            raise PriceError(f"Missing column '{col}' in OHLC data for {symbol}")

    return df


# ---------------- public API ----------------

def get_last_price(raw_symbol: str, use_cache: bool = True) -> PriceResult:
    """
    Normalize -> fetch -> cache.
    - US/most non-JPX: includes pre/after-hours when available.
    - JPX (.T): regular session only (Yahoo has no pre/post).
    Raises PriceError on failures.
    """
    symbol = normalize_symbol(raw_symbol)
    if not symbol:
        raise PriceError("Empty ticker.")

    now = time.time()
    if use_cache and symbol in _CACHE and (now - _CACHE[symbol].asof) < _TTL:
        return _CACHE[symbol]

    px = _fetch_yfinance(symbol)
    if px is None:
        raise PriceError(f"No price returned for {symbol}.")

    res = PriceResult(symbol=symbol, price=float(px), asof=now)
    _CACHE[symbol] = res
    return res
