# ---------------------------------------------------------------------
# status.py
# app/views/status.py
# Version and healthcheck endpoint for external tools.
# ---------------------------------------------------------------------

import os
from flask import Blueprint, render_template, jsonify, send_from_directory, current_app
from app.utils.logging import log_exception_with_traceback, log_info_message
from app.config import APP_VERSION

bp = Blueprint("status", __name__, url_prefix="/status")  # ← explicit prefix

# ---------------------------------------------------------------------
# View: View health and status
# ---------------------------------------------------------------------
@bp.route("/", methods=["GET"])
def health_and_version():
    """
    Endpoint for external tools to check the version and health of the application.
    Returns a JSON response with application version and status.
    """
    try:
        log_info_message(f"Healthcheck accessed. Returning version={APP_VERSION}")
        return jsonify({"status": "ok", "version": APP_VERSION})
    except Exception as e:
        log_exception_with_traceback("Error generating healthcheck response", e)
        return jsonify({"status": "error", "version": "unknown"}), 500


# ---------------------------------------------------------------------
# Route: Serve favicon at /grylli/status/favicon.ico
# ---------------------------------------------------------------------
@bp.route("/favicon.ico")
def root_favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, "static", "icons"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# ---------------------------------------------------------------------
# Route: Serve html view at /grylli/status/html
# ---------------------------------------------------------------------
@bp.route("/html", methods=["GET"])
def health_and_version_html():
    """
    Browser-accessible HTML view of healthcheck version info.
    """
    try:
        return render_template("status.html", version=APP_VERSION)
    except Exception as e:
        log_exception_with_traceback("Error rendering HTML healthcheck", e)
        return render_template("status.html", version="unknown"), 500
