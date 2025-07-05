# ---------------------------------------------------------------------
# backups.py
# app/views/backups.py
# Admin backup management views for Grylli.
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
    url_for,
)
from flask_babel import _
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.services.scheduler.backup_utils import create_backup, delete_old_backups, get_backup_files
from app.utils.logging import log_exception_with_traceback, log_info_message
from app.views.auth import admin_required

bp = Blueprint("backups", __name__)


# ---------------------------------------------------------------------
# View: List all backups
# ---------------------------------------------------------------------
@bp.route("overview/", strict_slashes=False)
@login_required
@admin_required
def list_backups():
    log_info_message(f"Admin '{current_user.username}' accessed backups overview dashboard.")
    delete_old_backups()
    backups = get_backup_files()

    if request.headers.get("HX-Request") == "true":
        return render_template("admin/partials/_list_backups_inner.html", backups=backups)

    return render_template("admin/list_backups.html", backups=backups)


# ---------------------------------------------------------------------
# View: Trigger new backup
# ---------------------------------------------------------------------
@bp.route("create", methods=["POST"], strict_slashes=False)
@login_required
@admin_required
def create_backup_view():
    try:
        backup_path = create_backup()
        flash(
            _("Backup created: %(filename)s") % {"filename": os.path.basename(backup_path)},
            "success",
        )
        log_info_message(f"Backup created by '{current_user.username}': {backup_path}")
    except Exception as e:
        flash(_("Failed to create backup."), "danger")
        log_exception_with_traceback("Failed to create backup", e)

    backups = get_backup_files()
    if request.headers.get("HX-Request") == "true":
        return render_template("admin/partials/backup_table_wrapper.html", backups=backups)
    return redirect(url_for("backups.list_backups"))


# ---------------------------------------------------------------------
# View: Delete a specific backup
# ---------------------------------------------------------------------
@bp.route("delete/<filename>", methods=["POST"], strict_slashes=False)
@login_required
@admin_required
def delete_backup(filename):
    try:
        backup_dir = os.path.abspath(current_app.config["BACKUP_DIR"])
        safe_filename = secure_filename(filename)
        full_path = os.path.abspath(os.path.join(backup_dir, safe_filename))

        if not full_path.startswith(backup_dir + os.sep):
            flash(_("Invalid backup filename."), "danger")
            log_info_message(
                f"Blocked attempted path traversal by '{current_user.username}': {filename}"
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
    except Exception as e:
        flash(_("Failed to delete backup."), "danger")
        log_exception_with_traceback(
            f"User '{current_user.username}' failed to delete backup '{filename}'", e
        )

    backups = get_backup_files()

    # HTMX request — return partial with trigger header
    if request.headers.get("HX-Request") == "true":
        rendered = render_template("admin/partials/backup_table.html", backups=backups)
        response = make_response(rendered)
        response.headers["HX-Trigger"] = "backup-updated"
        return response

    # Fallback full-page redirect
    return redirect(url_for("backups.list_backups"))
