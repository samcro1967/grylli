# ---------------------------------------------------------------------
# tasks.py
# app/views/tasks.py
# Routes to manually trigger admin-only system tasks.
# ---------------------------------------------------------------------

import subprocess

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.utils.logging import log_exception_with_traceback, log_info_message
from app.views.auth import admin_required

bp = Blueprint("tasks", __name__)


# ---------------------------------------------------------------------
# View: Admin Tasks Overview (GET)
# ---------------------------------------------------------------------
@bp.route("overview/", methods=["GET"], strict_slashes=False)
@login_required
@admin_required
def task_overview():
    """
    Render the Admin Tasks UI with available manual jobs.
    Returns a full or partial template depending on HTMX headers.
    """
    log_info_message(f"Admin '{current_user.username}' viewed the Task Runner page.")

    template = (
        "admin/tasks_partial.html" if "HX-Request" in request.headers else "admin/tasks_full.html"
    )
    return render_template(template)


# ---------------------------------------------------------------------
# Run: Check for new Grylli version (POST)
# ---------------------------------------------------------------------
@bp.route("check-version", methods=["POST"], strict_slashes=False)
@login_required
@admin_required
def check_version():
    """
    Run the version check task manually and capture its output.
    """
    log_info_message(f"Admin '{current_user.username}' triggered a manual version check.")

    try:
        result = subprocess.run(
            ["python3", "-m", "app.services.scheduler.version_check"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            flash("✅ Version check completed successfully.", "success")
            log_info_message(f"Version check output:\n{result.stdout.strip()}")
        else:
            flash("⚠️ Version check failed. Check logs for details.", "error")
            log_info_message(f"Version check error output:\n{result.stderr.strip()}")

    except Exception as e:
        flash("❌ An error occurred while checking version.", "error")
        log_exception_with_traceback("Manual version check failed", e)

    return redirect(url_for("tasks.task_overview"))
