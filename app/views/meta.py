# app/views/meta.py

from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from app.services.meta_utils import read_version_status, record_theme_change
from app.config import BACKGROUND_PATTERNS

bp = Blueprint("meta", __name__)


@bp.route("version/status", strict_slashes=False)
def version_status():
    return _version_status_impl()


def _version_status_impl():
    return jsonify(read_version_status())


@bp.route("/log-theme-change", methods=["POST"])
def log_theme_change():
    """
    Auth-required in production, open during test.
    """
    try:
        data = request.get_json()
        username = getattr(current_user, "username", "anonymous")
        record_theme_change(data.get("theme", ""), username)
        return jsonify(success=True)
    except Exception as e:
        from app.utils.logging import log_exception_with_traceback
        log_exception_with_traceback("Theme change logging failed", e)
        return jsonify(success=False), 500

@bp.route("/static/background-patterns.json")
def background_patterns():
    return jsonify(BACKGROUND_PATTERNS), 200, {'Content-Type': 'application/json; charset=utf-8'}

