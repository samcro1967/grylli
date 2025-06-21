# ---------------------------------------------------------------------
# status.py
# app/views/status.py
# Version and healthcheck endpoint for external tools.
# ---------------------------------------------------------------------

import os

from flask import Blueprint, current_app, jsonify, render_template, send_from_directory

from app.utils.logging import log_exception_with_traceback, log_info_message

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
        version = current_app.config.get("APP_VERSION", "unknown")
        log_info_message(f"Healthcheck accessed. Returning version={version}")
        return jsonify({"status": "ok", "version": version})
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
        version = current_app.config.get("APP_VERSION", "unknown")
        return render_template("status.html", version=version)
    except Exception as e:
        log_exception_with_traceback("Error rendering HTML healthcheck", e)
        return render_template("status.html", version="unknown"), 500
