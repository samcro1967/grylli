# ---------------------------------------------------------------------
# tools.py
# app/views/tools.py
# Admin tools view (tabbed layout for backups and scheduled tasks)
# ---------------------------------------------------------------------

import os
from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for
)
from flask_babel import _
from flask_login import current_user, login_required

from app.utils.logging import log_exception_with_traceback, log_info_message
from app.services.scheduler.backup_utils import get_backup_files
from werkzeug.utils import secure_filename
from app.views.auth import admin_required

bp = Blueprint("tools", __name__, url_prefix="/admin/tools")

TEST_HOOKS = {
    "override_backups": None,  # optional list of backups to return
    "skip_delete": False,      # skip file deletion logic
    "force_error": False       # raise exception if True
}


# ---------------------------------------------------------------------
# Route: Full Tools Page (with tabs)
# ---------------------------------------------------------------------
@bp.route("/", strict_slashes=False)
@admin_required
@login_required
def tools_full():
    try:
        log_info_message(f"Access - {current_user.username} - Tools")
        active_tab = request.args.get("tab", "backups")

        if request.headers.get("HX-Request"):
            return render_template("admin/tools/tools_tabs.html", active_tab=active_tab)

        return render_template("admin/tools/tools_full.html", active_tab=active_tab)
    except Exception as e:
        log_exception_with_traceback("Failed to load tools page", e)
        return "", 204


# ---------------------------------------------------------------------
# Route: Create a new backup (Tools tab)
# ---------------------------------------------------------------------
@bp.route("/backups/create", methods=["POST"], strict_slashes=False)
@admin_required
@login_required
def create_backup_view():
    from flask import flash, make_response
    from app.services.scheduler.backup_utils import create_backup, get_backup_files
    import os

    try:
        if TEST_HOOKS.get("force_error"):
            raise Exception("Forced error for test coverage")
        backup_path = create_backup()
        flash(_("Backup created: %(filename)s") % {"filename": os.path.basename(backup_path)}, "success")
        log_info_message(f"Backup created by '{current_user.username}': {backup_path}")
    except Exception as e:
        flash(_("Failed to create backup."), "danger")
        log_exception_with_traceback("Failed to create backup", e)

    backups = TEST_HOOKS["override_backups"] or get_backup_files()
    if request.headers.get("HX-Request") == "true":
        return render_template("admin/tools/partials/backup_table_wrapper.html", backups=backups)

    return redirect(url_for("tools.tools_backups"))


# ---------------------------------------------------------------------
# Route: Backups Tab (partial)
# ---------------------------------------------------------------------
@bp.route("/backups/", strict_slashes=False)
@admin_required
@login_required
def tools_backups():
    try:
        log_info_message(f"Access - {current_user.username} - Tools > Backups")
        backups = TEST_HOOKS["override_backups"] or get_backup_files()

        if request.headers.get("HX-Request"):
            return render_template("admin/tools/tools_backups_partial.html", backups=backups)

        return render_template("admin/tools/tools_full.html", active_tab="backups")
    except Exception as e:
        log_exception_with_traceback("Failed to load tools > backups", e)
        return "", 204


# ---------------------------------------------------------------------
# Route: Tasks Tab (partial)
# ---------------------------------------------------------------------
@bp.route("/tasks/", strict_slashes=False)
@admin_required
@login_required
def tools_tasks():
    try:
        log_info_message(f"Access - {current_user.username} - Tools > Tasks")

        if request.headers.get("HX-Request"):
            return render_template("admin/tools/tools_tasks_partial.html")

        return render_template("admin/tools/tools_full.html", active_tab="tasks")
    except Exception as e:
        log_exception_with_traceback("Failed to load tools > tasks", e)
        return "", 204

# ---------------------------------------------------------------------
# Route: Delete a backup (Tools tab version)
# ---------------------------------------------------------------------
@bp.route("/backups/delete/<filename>", methods=["POST"], strict_slashes=False)
@admin_required
@login_required
def delete_backup(filename):
    from flask import flash, make_response
    from werkzeug.utils import secure_filename
    from app.services.scheduler.backup_utils import get_backup_files

    try:
        if TEST_HOOKS.get("force_error"):
            raise Exception("Forced error for test coverage")
        if TEST_HOOKS.get("skip_delete"):
            backups = TEST_HOOKS.get("override_backups") or get_backup_files()
        else:
            backup_dir = os.path.abspath(current_app.config["BACKUP_DIR"])
            safe_filename = secure_filename(filename)
            full_path = os.path.abspath(os.path.join(backup_dir, safe_filename))

            if not full_path.startswith(backup_dir + os.sep):
                flash(_("Invalid backup filename."), "danger")
                log_info_message(
                    f"Blocked path traversal by '{current_user.username}': {filename}"
                )
            elif os.path.exists(full_path):
                os.remove(full_path)
                flash(_("Backup deleted: %(filename)s") % {"filename": safe_filename}, "success")
                log_info_message(f"Backup deleted by '{current_user.username}': {safe_filename}")
            else:
                flash(_("Backup file not found."), "warning")
                log_info_message(
                    f"User '{current_user.username}' attempted to delete missing backup: {safe_filename}"
                )

            backups = get_backup_files()

        if request.headers.get("HX-Request") == "true":
            rendered = render_template("admin/tools/partials/backup_table.html", backups=backups)
            response = make_response(rendered)
            response.headers["HX-Trigger"] = "backup-updated"
            return response

        return redirect(url_for("tools.tools_backups"))

    except Exception as e:
        flash(_("Failed to delete backup."), "danger")
        log_exception_with_traceback(
            f"User '{current_user.username}' failed to delete backup '{filename}'", e
        )
        return "", 204


# ---------------------------------------------------------------------
# Route: Manual version check task (Tools tab)
# ---------------------------------------------------------------------
@bp.route("/tasks/check-version", methods=["POST"], strict_slashes=False)
@admin_required
@login_required
def check_version():
    import subprocess
    from flask import flash, redirect

    log_info_message(f"Admin '{current_user.username}' triggered a manual version check.")

    try:
        if TEST_HOOKS.get("force_error"):
            raise Exception("Forced error for test coverage")
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

    return redirect(url_for("tools.tools_tasks"))
