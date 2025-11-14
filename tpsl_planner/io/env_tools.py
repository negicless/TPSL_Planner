# tpsl_app/env_tools.py
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PyQt5.QtWidgets import QMessageBox

APP_NAME = "tpsl_planner"


# ---------- Canonical .env location ----------

def env_path() -> Path:
    """
    Return the correct .env path for both EXE and dev mode.

    - Dev (python -m tpsl_app):
        <project_root>/.env

    - PyInstaller EXE:
        ~/Documents/tpsl_planner/.env
    """
    # If running as a PyInstaller EXE
    if getattr(sys, "frozen", False):
        docs = Path.home() / "Documents" / APP_NAME
        docs.mkdir(parents=True, exist_ok=True)
        return docs / ".env"

    # Dev mode: keep .env inside project root
    # env_tools.py -> tpsl_app/ -> project root is two levels up
    return Path(__file__).resolve().parents[2] / ".env"


# ---------- .env handling with UI ----------

def ensure_env_file(parent=None) -> None:
    """
    Ensures .env exists at env_path() and loads it.
    - Silent if found
    - Prompts user if missing
    """
    p = env_path()

    if not p.exists():
        reply = QMessageBox.question(
            parent,
            "Missing .env File",
            f"No .env file was found at:\n{p}\n\nWould you like to create one?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                "# Environment file for TP-SL Planner\n"
                "NOTION_TOKEN=\n"
                "NOTION_TRADE_DB=\n"
                "TELEGRAM_TOKEN=\n"
                "YF_TIMEOUT=10\n"
                "LOG_LEVEL=INFO\n",
                encoding="utf-8",
            )
            QMessageBox.information(
                parent,
                "Created",
                f"A new .env file has been created at:\n{p}"
            )
        else:
            QMessageBox.warning(
                parent,
                "Environment Not Loaded",
                "Without a .env file, Notion or Telegram integration may not work."
            )

    # Always load (even if just created)
    load_dotenv(p, override=True)


# ---------- App config dir (for other config files, not .env) ----------

def app_config_dir() -> Path:
    """
    Windows -> %APPDATA%\\tpsl_planner
    macOS   -> ~/Library/Application Support/tpsl_planner
    Linux   -> ~/.config/tpsl_planner  (or $XDG_CONFIG_HOME/tpsl_planner)
    """
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    d = base / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def env_file_path() -> Path:
    """
    Backwards-compat helper: now just points to env_path().
    """
    return env_path()


def load_env() -> None:
    """
    Load (or reload) the .env file.
    """
    load_dotenv(env_file_path(), override=True)


def ensure_env_template() -> bool:
    """
    Ensure an .env template exists at env_file_path().
    Returns True if a new file was created, False if it already existed.
    """
    p = env_file_path()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "NOTION_TOKEN=\n"
            "NOTION_TRADE_DB=\n"
            "TELEGRAM_TOKEN=\n"
            "YF_TIMEOUT=10\n"
            "LOG_LEVEL=INFO\n",
            encoding="utf-8",
        )
        return True
    return False

def has_valid_env() -> bool:
    """
    Returns True only if .env exists and required tokens are filled.
    """
    env_file = env_path()
    if not env_file.exists():
        return False

    content = env_file.read_text(encoding="utf-8")
    # 必須トークン（必要なものをここでチェック）
    required = ["NOTION_TOKEN", "NOTION_TRADE_DB"]

    for key in required:
        if f"{key}=" in content:
            # e.g. NOTION_TOKEN=
            line = [x for x in content.splitlines() if x.startswith(key)]
            if line:
                value = line[0].split("=",1)[1].strip()
                if not value:   # 空欄ならアウト
                    return False

    return True
