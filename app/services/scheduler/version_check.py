"""
# ---------------------------------------------------------------------
# version_check.py
# app/services/scheduler/version_check.py
# Version check scheduled job
# ---------------------------------------------------------------------
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from app.config import APP_VERSION, DATA_DIR, GITHUB_URL
from app.utils.logging import log_exception_with_traceback, log_info_message

# Derive API URL from GitHub repo
REPO_PATH = GITHUB_URL.rstrip("/").replace("https://github.com/", "")
GITHUB_API_RELEASES = f"https://api.github.com/repos/{REPO_PATH}/releases/latest"

# Output path for cached version data
VERSION_CACHE_PATH = Path(DATA_DIR) / "version_status.json"


def write_version_cache(current, latest, url):
    VERSION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    VERSION_CACHE_PATH.write_text(
        json.dumps(
            {
                "current_version": current,
                "latest_version": latest,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "github_url": url,
            },
            indent=2,
        )
    )


def check_latest_version():
    """
    Periodically checks GitHub for the latest release and logs a message if a newer version is available.
    Writes status to a persistent JSON file for UI access.
    """
    try:
        response = requests.get(GITHUB_API_RELEASES, timeout=10)
        response.raise_for_status()
        latest = response.json().get("tag_name", "").lstrip("v")

        if not latest:
            log_info_message("⚠️ Could not parse latest version from GitHub response.")
            write_version_cache(APP_VERSION, None, GITHUB_URL)
            return

        if latest != APP_VERSION:
            log_info_message(
                f"🔔 A new Grylli version is available: v{latest} "
                f"(currently running: v{APP_VERSION}) — {GITHUB_URL}/releases"
            )
        else:
            log_info_message(f"✅ Grylli is up to date (v{APP_VERSION})")

        write_version_cache(APP_VERSION, latest, GITHUB_URL)

    except Exception as e:
        log_exception_with_traceback("Failed to check latest Grylli version", e)
        write_version_cache(APP_VERSION, None, GITHUB_URL)


if __name__ == "__main__":
    check_latest_version()
