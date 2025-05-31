"""
# ---------------------------------------------------------------------
# status.py
# app/views/status.py
# Version and healthcheck endpoint for external tools.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, current_app, jsonify

bp = Blueprint("status", __name__)


@bp.route("/", methods=["GET"])
def health_and_version():
    """
    Endpoint for external tools to check the version and health of the application.

    Returns:
        A JSON response with the application version and a status of "ok".
    """
    return jsonify({"status": "ok", "version": current_app.config.get("APP_VERSION", "unknown")})
