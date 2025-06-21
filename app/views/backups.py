# ---------------------------------------------------------------------
# backups.py
# app/views/backups.py
# Admin backup management views for Grylli.
# ---------------------------------------------------------------------

import os

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
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
@bp.route("/")
@login_required
@admin_required
def list_backups():
    """
    View: List all backups
    ======================

    Lists all backups in the backup directory, sorted newest first.

    Notes:
        - Automatically deletes old backups according to the configured
          retention period.
        - Renders the `admin/list_backups.html` template with the list of
          backups.
    """
    delete_old_backups()
    backups = get_backup_files()
    return render_template("admin/list_backups.html", backups=backups)


# ---------------------------------------------------------------------
# View: Trigger new backup
# ---------------------------------------------------------------------
@bp.route("/create")
@login_required
@admin_required
def create_backup_view():
    """
    View: Trigger new backup
    ========================

    Creates a new backup of the application's database and logs the action.

    Notes:
        - Utilizes the `create_backup` utility to generate the backup.
        - Displays a success message upon successful creation.
        - Handles and logs exceptions if the backup creation fails.

    :returns: Redirects to the list of backups view.
    """
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

    return redirect(url_for("backups.list_backups"))


# ---------------------------------------------------------------------
# View: Delete a specific backup
# ---------------------------------------------------------------------
@bp.route("/delete/<filename>", methods=["POST"])
@login_required
@admin_required
def delete_backup(filename):
    """
    View: Delete a specific backup (secured)
    ========================================

    Deletes a backup file only if it's within the BACKUP_DIR and passes
    validation to prevent path traversal attacks.

    :param filename: The name of the backup file to delete.
    :returns: Redirects to the backup list.
    """
    try:
        backup_dir = os.path.abspath(current_app.config["BACKUP_DIR"])
        safe_filename = secure_filename(filename)  # Strips unsafe characters
        full_path = os.path.abspath(os.path.join(backup_dir, safe_filename))

        # Ensure resolved path is inside BACKUP_DIR
        if not full_path.startswith(backup_dir + os.sep):
            flash(_("Invalid backup filename."), "danger")
            log_info_message(f"Blocked attempted path traversal by '{current_user.username}': {filename}")
            return redirect(url_for("backups.list_backups"))

        if os.path.exists(full_path):
            os.remove(full_path)
            flash(_("Backup deleted: %(filename)s") % {"filename": safe_filename}, "success")
            log_info_message(f"Backup deleted by '{current_user.username}': {safe_filename}")
        else:
            flash(_("Backup file not found."), "warning")
            log_info_message(f"Backup deletion attempted but file not found: {safe_filename}")
    except Exception as e:
        flash(_("Failed to delete backup."), "danger")
        log_exception_with_traceback(f"Failed to delete backup '{filename}'", e)

    return redirect(url_for("backups.list_backups"))
