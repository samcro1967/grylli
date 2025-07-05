# app/views/meta.py
import json
from pathlib import Path

from flask import Blueprint, jsonify

from app.config import APP_VERSION, DATA_DIR, GITHUB_URL

bp = Blueprint("meta", __name__)


@bp.route("version/status", strict_slashes=False)
def version_status():
    cache_path = Path(DATA_DIR) / "version_status.json"
    if cache_path.exists():
        try:
            return jsonify(json.loads(cache_path.read_text()))
        except Exception:
            pass  # fallback below

    # fallback if cache is missing or broken
    return jsonify(
        {
            "current_version": APP_VERSION,
            "latest_version": None,
            "timestamp": None,
            "github_url": GITHUB_URL,
            "error": "version cache missing or unreadable",
        }
    )
