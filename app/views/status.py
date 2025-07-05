# ---------------------------------------------------------------------
# status.py
# app/views/status.py
# Version and healthcheck endpoint for external tools.
# ---------------------------------------------------------------------

import os

from flask import Blueprint, current_app, jsonify, render_template, send_from_directory

from app.config import APP_VERSION
from app.utils.logging import log_exception_with_traceback, log_info_message

bp = Blueprint("status", __name__, url_prefix="/status")


# ---------------------------------------------------------------------
# View: View health and status
# ---------------------------------------------------------------------
@bp.route("", methods=["GET"], strict_slashes=False)
def health_and_version():
    """
    Endpoint for external tools to check the version and health of the application.
    Returns a JSON response with application version and status.
    """
    try:
        log_info_message(f"Healthcheck accessed. Returning version={APP_VERSION}")
        return jsonify({"status": "ok", "version": APP_VERSION})
    except Exception as e:
        log_exception_with_traceback("Error generating healthcheck JSON response", e)
        return jsonify({"status": "error", "version": "unknown"}), 500


# ---------------------------------------------------------------------
# Route: Serve favicon at /grylli/status/favicon.ico
# ---------------------------------------------------------------------
@bp.route("favicon.ico", strict_slashes=False)
def root_favicon():
    """
    Serve the favicon for the status route.
    """
    try:
        return send_from_directory(
            os.path.join(current_app.root_path, "static", "icons"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )
    except Exception as e:
        log_exception_with_traceback("Error serving favicon from status route", e)
        return "", 404


# ---------------------------------------------------------------------
# Route: Serve html view at /grylli/status/html
# ---------------------------------------------------------------------
@bp.route("html", methods=["GET"], strict_slashes=False)
def health_and_version_html():
    """
    Browser-accessible HTML view of healthcheck version info.
    """
    try:
        log_info_message(f"Healthcheck HTML page accessed. Version={APP_VERSION}")
        return render_template("status.html", version=APP_VERSION)
    except Exception as e:
        log_exception_with_traceback("Error rendering HTML healthcheck page", e)
        return render_template("status.html", version="unknown"), 500
