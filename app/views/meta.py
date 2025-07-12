# ---------------------------------------------------------------------
# meta.py
# app/views/meta.py
# Routes for exposing application metadata and user event logging.
# ---------------------------------------------------------------------

import json
from pathlib import Path

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.config import APP_VERSION, DATA_DIR, GITHUB_URL
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("meta", __name__)


# ---------------------------------------------------------------------
# Version status API route
# ---------------------------------------------------------------------
@bp.route("version/status", strict_slashes=False)
def version_status():
    """
    Return the current and latest application version.

    Attempts to read from cached file at DATA_DIR/version_status.json.
    Falls back to basic version info if file is missing or unreadable.
    """
    cache_path = Path(DATA_DIR) / "version_status.json"
    if cache_path.exists():
        try:
            return jsonify(json.loads(cache_path.read_text()))
        except Exception as e:
            log_exception_with_traceback("Failed to read version status cache", e)

    return jsonify(
        {
            "current_version": APP_VERSION,
            "latest_version": None,
            "timestamp": None,
            "github_url": GITHUB_URL,
            "error": "version cache missing or unreadable",
        }
    )


# ---------------------------------------------------------------------
# Log theme change (client-side event)
# ---------------------------------------------------------------------
@bp.route("/log-theme-change", methods=["POST"])
@login_required
def log_theme_change():
    """
    Logs a theme switch event triggered by the user from the front-end.
    """
    try:
        data = request.get_json()
        theme = data.get("theme", "").strip()

        if theme:
            log_info_message(f"Access - {current_user.username} - Switched theme to '{theme}'")

        return jsonify(success=True)

    except Exception as e:
        log_exception_with_traceback("Theme change logging failed", e)
        return jsonify(success=False), 500
