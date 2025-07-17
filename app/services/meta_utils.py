# app/services/meta_utils.py

import json
from pathlib import Path
from app.config import DATA_DIR, APP_VERSION, GITHUB_URL
from app.utils.logging import log_exception_with_traceback, log_info_message


def read_version_status():
    cache_path = Path(DATA_DIR) / "version_status.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except Exception as e:
            log_exception_with_traceback("Failed to read version status cache", e)

    return {
        "current_version": APP_VERSION,
        "latest_version": None,
        "timestamp": None,
        "github_url": GITHUB_URL,
        "error": "version cache missing or unreadable",
    }


def record_theme_change(theme: str, username: str):
    theme = theme.strip()
    if theme:
        log_info_message(f"Access - {username} - Switched theme to '{theme}'")
