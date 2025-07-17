# ---------------------------------------------------------------------
# system_info.py
# app/views/system_info.py
# Blueprint for system and stack info display (Grylli diagnostics).
# ---------------------------------------------------------------------

import json
import os
import platform
import shutil
import sqlite3
import subprocess
from importlib.metadata import PackageNotFoundError, version

from flask import Blueprint, current_app, render_template, request
from flask_login import current_user, login_required

from app.utils.logging import (
    log_debug_message,
    log_exception_with_traceback,
    log_info_message,
)

bp = Blueprint("system_info", __name__)


# ---------------------------------------------------------------------
# Helper to get version safely
# ---------------------------------------------------------------------
def safe_version(pkg_name):
    """
    Safely get the version of a package.
    """
    try:
        return version(pkg_name)
    except PackageNotFoundError:
        return "Not installed"
    except Exception as e:
        log_exception_with_traceback(f"Failed to get version for package '{pkg_name}'", e)
        return "Unavailable"


# ---------------------------------------------------------------------
# Get CLI version (e.g., pip, apprise)
# ---------------------------------------------------------------------
def get_cli_version(command_str):
    """
    Executes a CLI command and retrieves its version information, safely.
    Supports commands like "pip --version" or "apprise --version".
    """
    try:
        command_parts = command_str.split()
        binary = command_parts[0]

        if shutil.which(binary) is None:
            return "Unavailable"

        output = subprocess.check_output(command_parts).decode().strip()
        return output.splitlines()[0]
    except Exception as e:
        log_exception_with_traceback(f"Failed to run CLI version command: {command_str}", e)
        return "Unavailable"


# ---------------------------------------------------------------------
# View:  System Info
# ---------------------------------------------------------------------
@bp.route("system-info", strict_slashes=False)
@login_required
def index():
    """
    Render system and stack diagnostics for admins and developers.
    Renders a full or partial template based on HTMX headers.
    """
    try:
        log_info_message(f"Access - {current_user.username} - System Info")

        stack = {
            "Python": platform.python_version(),
            "pip": get_cli_version("pip --version"),
            "SQLite": sqlite3.sqlite_version,
            "Flask": safe_version("flask"),
            "Flask-WTF": safe_version("flask-wtf"),
            "Flask-Login": safe_version("flask-login"),
            "Flask-Migrate": safe_version("flask-migrate"),
            "Flask-Babel": safe_version("flask-babel"),
            "Jinja2": safe_version("jinja2"),
            "SQLAlchemy": safe_version("sqlalchemy"),
            "Gunicorn": safe_version("gunicorn"),
            "Email Validator": safe_version("email-validator"),
            "Cryptography": safe_version("cryptography"),
            "APScheduler": safe_version("apscheduler"),
            "Apprise (Python)": safe_version("apprise"),
            "Apprise CLI": get_cli_version("apprise --version"),
        }

        version_json_path = os.path.join(current_app.root_path, "static", "version.json")
        if os.path.exists(version_json_path):
            try:
                with open(version_json_path, "r") as f:
                    frontend_versions = json.load(f)
                stack.update(frontend_versions)
                log_debug_message("Frontend version.json loaded and merged.")
            except Exception as e:
                log_exception_with_traceback("Error reading version.json", e)
                stack["Node.js"] = "Unavailable"
                stack["npm"] = "Unavailable"
        else:
            stack["Node.js"] = "Unavailable"
            stack["npm"] = "Unavailable"
            log_info_message(
                "Frontend version.json not found. Node.js/npm versions set to 'Unavailable'."
            )

        template = (
            "system_info_partial.html"
            if request.headers.get("HX-Request")
            else "system_info_full.html"
        )
        return render_template(template, stack=stack)

    except Exception as e:
        log_exception_with_traceback("Error rendering System Info page", e)
        stack = {"Error": "Failed to load system info"}
        template = (
            "system_info_partial.html"
            if request.headers.get("HX-Request")
            else "system_info_full.html"
        )
        return render_template(template, stack=stack)
