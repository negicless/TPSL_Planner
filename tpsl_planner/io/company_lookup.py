# tpsl_app/company_lookup.py
from __future__ import annotations
import os, sys, json
from functools import lru_cache
import re, requests

# Optional online lookup
try:
    import yfinance as yf
except Exception:
    yf = None  # still works offline with cache

# --- JP ticker pattern: 4 digits OR 3 digits + letter (e.g. 147A) ---
JP_TICKER_PATTERN = re.compile(r"^(?:\d{4}|\d{3}[A-Z])$")


def _looks_english(s: str | None) -> bool:
    if not s:
        return True
    # True if all ASCII (no Japanese chars)
    return all(ord(ch) < 128 for ch in s)


# ---------- paths that work in dev and PyInstaller onefile ----------
def _app_dir() -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


def _cache_path() -> str:
    return os.path.join(_app_dir(), "ticker_cache.json")


def _seed_path() -> str:
    # Ship a small starter dictionary (optional). You can expand it over time.
    return os.path.join(_app_dir(), "ticker_seed.json")


# ---------- small read/write helpers ----------
def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------- normalization & market inference ----------
def normalize_ticker(code: str, market_hint: str | None = None) -> str:
    """Normalize raw user input to a Yahoo-style ticker."""
    if not code:
        return ""
    t = code.strip().upper()

    # If already has a dot suffix, keep it (AAPL, AAPL.NE, 7203.T, 147A.T)
    if "." in t:
        return t

    # JP cash equity codes:
    # - 4 digits: 7203
    # - 3 digits + 1 letter: 147A
    if JP_TICKER_PATTERN.fullmatch(t):
        return t + ".T"

    # Simple hint path for JP/US (fallback if caller says "JP")
    if market_hint == "JP" and t.isalnum() and not t.endswith(".T"):
        return t + ".T"

    # Otherwise leave as-is (US tickers etc.)
    return t



def infer_market(t: str) -> str:
    if not t:
        return "US"
    s = t.strip().upper()
    if s.endswith(".T"):
        return "JP"
    # raw JP code without .T: 7203 or 147A
    if JP_TICKER_PATTERN.fullmatch(s):
        return "JP"
    return "US"



# ---------- main API ----------
@lru_cache(maxsize=4096)
def get_company_name(ticker: str) -> str:
    """Return a friendly company name; JP tickers prefer Japanese names."""
    if not ticker:
        return ""

    t = normalize_ticker(ticker)

    # 0) read on-disk cache
    cache = _read_json(_cache_path())
    cached = cache.get(t)

    # is this a JP ticker we understand? (7203.T / 147A.T)
    is_jp = t.endswith(".T") and JP_TICKER_PATTERN.fullmatch(t[:-2])

    # ---------- JP path FIRST (and fix old English cache) ----------
    if is_jp:
        # If cache has JP (non-ASCII), return it immediately
        if cached and not _looks_english(cached):
            return cached

        try:
            yj_code = t[:-2]  # strip ".T" -> "8058" or "147A"
            url = f"https://finance.yahoo.co.jp/quote/{yj_code}.T"
            res = requests.get(
                url,
                timeout=6,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0 Safari/537.36"
                    ),
                    "Accept-Language": "ja,en;q=0.8",
                    "Referer": "https://finance.yahoo.co.jp/",
                },
            )
            if res.ok:
                # 1) get the full <title>...</title> text
                m = re.search(r"<title>\s*([^<]+?)</title>", res.text, re.IGNORECASE)
                if m:
                    title = m.group(1).strip()

                    # 2) drop trailing " - Yahoo!ファイナンス ..."
                    title = re.sub(r"\s*-\s*Yahoo!ファイナンス.*$", "", title)

                    # 3) drop suffix like "の株価・株式情報", "：株価…", "株価…" etc
                    title = re.sub(r"(の株価.*|：株価.*|株価・株式情報.*|株価.*)$", "", title)

                    # 4) drop code parts like (8058), 【147A】, 〖147A〗 etc
                    title = re.sub(r"[（(【〖]\s*[\dA-Z.]+[）)】〗]", "", title)

                    # 5) drop leading legal prefixes like "(株)"
                    title = re.sub(r"^\s*\(株\)\s*", "", title)

                    jp_name = title.strip()
                    if jp_name:
                        cache[t] = jp_name
                        _write_json(_cache_path(), cache)
                        return jp_name

        except Exception:
            # If JP fetch failed, fall through to seed / yfinance
            pass

    # ---------- Seed (offline) ----------
    seed = _read_json(_seed_path())
    if t in seed:
        name = seed[t]
        # If JP ticker and seed is Japanese, persist to cache
        if is_jp and not _looks_english(name):
            cache[t] = name
            _write_json(_cache_path(), cache)
        return name

    # ---------- yfinance fallback (usually English) ----------
    name = None
    if yf is not None:
        try:
            info = yf.Ticker(t).info
            name = (info.get("longName") or info.get("shortName") or "").strip()
        except Exception:
            name = None

    # Persist what we found (even if English), but JP path above will overwrite later with JP
    final = name or t
    cache[t] = final
    _write_json(_cache_path(), cache)
    return final


def display_label(ticker: str) -> str:
    """Human-friendly 'TICKER — Company Name' for reports."""
    t = normalize_ticker(ticker)
    name = get_company_name(t)
    if name and name != t:
        return f"{t} — {name}"
    return t


# Backward-compat alias so older imports keep working
def lookup_company_name(ticker: str) -> str:
    return get_company_name(ticker)


__all__ = [
    "normalize_ticker",
    "get_company_name",
    "display_label",
    "lookup_company_name",
]


@lru_cache(maxsize=2048)
def get_company_sector(ticker: str) -> str:
    """Return a best-effort sector/industry string for `ticker`.

    Tries (in order):
    - yfinance `info['sector']` or `info['industry']` when `yfinance` is available
    - seed/cache lookup if available (rare)
    - empty string on failure
    """
    if not ticker:
        return ""
    t = normalize_ticker(ticker)
    # 1) try seed/cache (if seed contains sector info it would be stored specially,
    # but for now we prioritize yfinance)
    try:
        if yf is not None:
            try:
                info = yf.Ticker(t).info or {}
                sec = info.get("sector") or info.get("industry") or ""
                if isinstance(sec, str) and sec:
                    return sec.strip()
            except Exception:
                pass
    except Exception:
        pass

    # fallback: no sector known
    return ""


def display_ticker(t: str) -> str:
    """Return clean display ticker (remove .T, .F, etc. for JP)."""
    if not t:
        return t
    if t.endswith(".T"):
        return t.replace(".T", "")
    return t
