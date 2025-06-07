"""
# ---------------------------------------------------------------------
# system_info.py
# app/views/system_info.py
# Blueprint for system and stack info display (Grylli diagnostics).
# ---------------------------------------------------------------------
"""

import json
import os
import platform
import sqlite3
import subprocess
from importlib.metadata import PackageNotFoundError, version

from flask import Blueprint, current_app, render_template
from flask_login import current_user, login_required

from app.utils.logging import log_debug_message, log_info_message

bp = Blueprint("system_info", __name__)


# ---------------------------------------------------------------------
# Helper to get version safely
# ---------------------------------------------------------------------
def safe_version(pkg_name):
    """
    Safely get the version of a package.

    Parameters
    ----------
    pkg_name : str
        Name of the package.

    Returns
    -------
    str
        The version string, or "Not installed" if the package is not installed.
    """
    try:
        return version(pkg_name)
    except PackageNotFoundError:
        return "Not installed"


# ---------------------------------------------------------------------
# Get client versions
# ---------------------------------------------------------------------
def get_cli_version(command):
    """
    Executes a CLI command and retrieves its version information.

    Parameters
    ----------
    command : str
        The command to execute for retrieving version information.

    Returns
    -------
    str
        The first line of the command output if successful, otherwise "Unavailable".
    """

    try:
        output = subprocess.check_output(command, shell=True).decode().strip()
        return output.splitlines()[0]  # Only first line
    except Exception:
        return "Unavailable"


# ---------------------------------------------------------------------
# View:  System Info
# ---------------------------------------------------------------------
@bp.route("/system-info")
@login_required
def index():
    log_info_message(f"User '{current_user.username}' accessed the System Info page.")

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

    # Load frontend versions from embedded version.json
    version_json_path = os.path.join(current_app.root_path, "static", "version.json")
    if os.path.exists(version_json_path):
        with open(version_json_path, "r") as f:
            frontend_versions = json.load(f)
        stack.update(frontend_versions)
        log_debug_message("Frontend version.json loaded and merged.")
    else:
        # Optionally add fallback or warning here
        stack["Node.js"] = "Unavailable"
        stack["npm"] = "Unavailable"
        log_info_message(
            "Frontend version.json not found. Node.js/npm versions set to 'Unavailable'."
        )
    return render_template("system_info.html", stack=stack)
