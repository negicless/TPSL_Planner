# tpsl_app/notion_client.py
import os, datetime, json, time
import requests
from functools import lru_cache
from .company_lookup import get_company_name, normalize_ticker

# --- Load .env in dev (won't override EXE env) ---
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=False)
except Exception:
    pass

# --- Force Requests to use certifi CA bundle (important for PyInstaller EXE) ---
try:
    import certifi
    _CA = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", _CA)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", _CA)
except Exception:
    _CA = True  # let Requests decide

# --- Config: read NOTION_TOKEN and NOTION_TRADE_DB from robust loader ---
try:
    from .config_loader import load_config
except ImportError:
    from tpsl_planner.io.config_loader import load_config  # fallback for script mode

NOTION_TOKEN, NOTION_DB_ID = load_config()  # returns (token, db_id)

API_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# --------------------------------------------------------------------------- #
# Schema helpers
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=4)
def _get_db_schema(dbid: str) -> dict:
    r = requests.get(
        f"https://api.notion.com/v1/databases/{dbid}",
        headers=API_HEADERS,
        timeout=20,
        verify=_CA,
    )
    r.raise_for_status()
    return r.json()

def _title_prop_name(db_json: dict) -> str:
    for name, prop in db_json.get("properties", {}).items():
        if prop.get("type") == "title":
            return name
    raise RuntimeError("No title property found in the target database.")

def _as_number_or_text(props_schema: dict, name: str, value):
    """If property is 'number', coerce to float; else fall back to rich_text if available."""
    if name not in props_schema:
        return {}
    t = props_schema[name].get("type")
    if t == "number":
        try:
            return {name: {"number": float(value)}}
        except Exception:
            return {}
    if t in ("rich_text", "text"):
        return {name: {"rich_text": [{"text": {"content": "" if value is None else str(value)}}]}}
    return {}

def _as_text(props_schema: dict, name: str, value):
    if name not in props_schema:
        return {}
    t = props_schema[name].get("type")
    if t in ("rich_text", "text"):
        return {name: {"rich_text": [{"text": {"content": "" if value is None else str(value)}}]}}
    return {}

def _as_select_or_text(props_schema: dict, name: str, value):
    if name not in props_schema:
        return {}
    t = props_schema[name].get("type")
    if t in ("select", "status") and value:
        return {name: {t: {"name": str(value)}}}
    if t in ("rich_text", "text"):
        return {name: {"rich_text": [{"text": {"content": "" if value is None else str(value)}}]}}
    return {}

def _set_status_default(props_schema: dict, value: str | None):
    """Set 'Status' property; default to 'Idea' when not provided, only if DB has Status."""
    if "Status" not in props_schema:
        return {}
    status_name = (value or "Idea").strip()
    return _as_select_or_text(props_schema, "Status", status_name)

def _as_date(props_schema: dict, name: str, date_str: str | None):
    if name not in props_schema:
        return {}
    t = props_schema[name].get("type")
    if t == "date" and date_str:
        return {name: {"date": {"start": date_str}}}
    return {}

def _md_to_blocks(md: str, chunk_limit: int = 1800) -> list[dict]:
    """
    Minimal Markdown→Notion blocks:
    - Splits on blank lines into paragraphs
    - Splits long paragraphs into safe chunks (~2000 char rich_text limit)
    """
    if not md:
        return []
    md = md.strip()
    blocks = []
    for para in md.split("\n\n"):
        text = para.replace("\t", "    ")
        while text:
            chunk = text[:chunk_limit]
            text = text[chunk_limit:]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
            })
    return blocks


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def send_trade_to_notion(
    trade: dict,
    report_text: str = "",
    *,
    markdown_to_body: bool = True,
    cover_url: str | None = None,
    image_url: str | None = None,
    icon_emoji: str | None = "🚀",
):
    """
    Create a Notion page for a trade.
    New features:
      - markdown_to_body: if True, put the report_text into page 'children' blocks
        so it renders on Gallery cards (instead of just a property).
      - cover_url: external URL (e.g., your chart in the image bucket) used as page cover.
      - image_url: optional image block inserted at top of the page body.
      - icon_emoji: optional page icon.

    Still writes all properties like before (Ticker/Company/Side/Entry/Stop/Target/Shares/R-Multiple/Status/Date).
    """
    if not NOTION_TOKEN or not NOTION_DB_ID:
        raise RuntimeError("Set NOTION_TOKEN and NOTION_TRADE_DB first.")

    db = _get_db_schema(NOTION_DB_ID)
    props_schema = db.get("properties", {})
    title_name = _title_prop_name(db)

    # --- ticker & company ---
    ticker_raw  = (trade.get("ticker") or "-").strip()
    ticker_norm = normalize_ticker(ticker_raw)
    company     = get_company_name(ticker_norm)
    from .company_lookup import display_ticker
    display_code = display_ticker(ticker_norm)

    # Title uses TICKER ONLY (keeps your clean card titles)
    props = {title_name: {"title": [{"text": {"content": display_code}}]}}

    # Optional 'Ticker' property
    if "Ticker" in props_schema:
        props.update(_as_select_or_text(props_schema, "Ticker", display_code))

    # Company property (supports "Company" or "Company Name")
    company_key = "Company" if "Company" in props_schema else ("Company Name" if "Company Name" in props_schema else None)
    if company_key:
        props.update(_as_select_or_text(props_schema, company_key, company))

    # Side / numbers
    props.update(_as_select_or_text(props_schema, "Side", trade.get("side", "Long")))
    props.update(_as_number_or_text(props_schema, "Entry",  trade.get("entry")))
    props.update(_as_number_or_text(props_schema, "Stop",   trade.get("stop")))
    props.update(_as_number_or_text(props_schema, "Target", trade.get("target")))
    props.update(_as_number_or_text(props_schema, "Shares", trade.get("shares")))

    # R-Multiple (2 decimals)
    r_val = trade.get("r")
    if r_val is not None:
        try:
            r_val = round(float(r_val), 2)
        except Exception:
            r_val = None
    props.update(_as_number_or_text(props_schema, "R-Multiple", r_val))

    # Section (select/text)
    if "Section" in props_schema:
        props.update(_as_select_or_text(props_schema, "Section", trade.get("section")))
    elif "Sector" in props_schema:
        props.update(_as_select_or_text(props_schema, "Sector", trade.get("section")))

    # Setup rating (handle multi_select, select, or text) — try common property names
    for _k in ("Setup Rating", "Setup rating", "Rating", "Setup"):
        if _k in props_schema:
            prop_type = props_schema[_k].get("type")
            val = trade.get("setup_rating")
            if prop_type == "multi_select" and val:
                # Notion expects a list of {name: ..} for multi_select
                try:
                    props.update({
                        _k: {"multi_select": [{"name": str(val)}]}
                    })
                except Exception:
                    pass
            else:
                # fallback to select/text handling
                props.update(_as_select_or_text(props_schema, _k, val))
            break

    # Setup rating numeric value (if DB has a number property for it)
    for _k in ("Setup Rating Value", "Setup rating value", "Rating Value", "setup_rating_value"):
        if _k in props_schema:
            props.update(_as_number_or_text(props_schema, _k, trade.get("setup_rating_value")))
            break

    # Default Status
    props.update(_set_status_default(props_schema, trade.get("status")))

    # Notes / Report properties (kept for filtering/search)
    if "Notes" in props_schema:
        props.update(_as_text(props_schema, "Notes", trade.get("notes", "")))
    if "Report" in props_schema:
        header = f"{display_code} — {company}\n" if company_key else ""
        props.update(_as_text(props_schema, "Report", header + (report_text or "")))

    # Date
    today = datetime.date.today().isoformat()
    props.update(_as_date(props_schema, "Date", today))

    # -------- Page body (children) + cover/icon ----------
    children = []
    if image_url:
        children.append({
            "object": "block",
            "type": "image",
            "image": {"type": "external", "external": {"url": image_url}},
        })
    if markdown_to_body and report_text:
        children.extend(_md_to_blocks(report_text))

    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": props,
    }
    if children:
        payload["children"] = children
    if cover_url:
        payload["cover"] = {"external": {"url": cover_url}}
    if icon_emoji:
        payload["icon"] = {"emoji": icon_emoji}

    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=API_HEADERS,
        json=payload,
        timeout=30,
        verify=_CA
    )
    if not r.ok:
        print("Create error:", r.status_code, r.text[:1200])
        r.raise_for_status()
    return r.json()

