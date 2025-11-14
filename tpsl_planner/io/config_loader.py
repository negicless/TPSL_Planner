# config_loader.py
from pathlib import Path
import os, sys
from dotenv import load_dotenv

def app_root() -> Path:
    # Works both in dev and in PyInstaller onefile
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def load_config():
    # 1) .env next to the EXE (preferred for portability)
    env_path = app_root() / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)

    # 2) fall back to system environment
    token = os.getenv("NOTION_TOKEN", "").strip()
    db_id  = os.getenv("NOTION_TRADE_DB", "").strip()

    problems = []
    if not token:
        problems.append("NOTION_TOKEN missing")
    if not db_id:
        problems.append("NOTION_TRADE_DB missing")

    if problems:
        raise RuntimeError(
            "Notion configuration error: " + ", ".join(problems) +
            "\nPlace a .env next to the EXE (or set system env vars):\n"
            "  NOTION_TOKEN=secret_...\n  NOTION_TRADE_DB=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
        )

    return token, db_id
