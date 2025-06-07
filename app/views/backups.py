"""
# ---------------------------------------------------------------------
# backups.py
# app/views/backups.py
# Admin backup management views for Grylli.
# ---------------------------------------------------------------------
"""

import os

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.services.scheduler.backup_utils import create_backup, delete_old_backups, get_backup_files
from app.utils.logging import log_error_message, log_info_message
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

    :returns: Rendered template for the list of backups.
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
        log_error_message(f"Failed to create backup: {e}")
    return redirect(url_for("backups.list_backups"))


# ---------------------------------------------------------------------
# View: Delete a specific backup
# ---------------------------------------------------------------------
@bp.route("/delete/<filename>")
@login_required
@admin_required
def delete_backup(filename):
    """
    View: Delete a specific backup
    ==============================

    Deletes a specific backup from the disk and logs the action.

    Notes:
        - Checks if the backup file exists before attempting deletion.
        - Handles and logs exceptions if the deletion fails.

    :param filename: The filename of the backup to be deleted.
    :returns: Redirects to the list of backups view.
    """
    path = os.path.join(current_app.config["BACKUP_DIR"], filename)
    try:
        if os.path.exists(path):
            os.remove(path)
            flash(_("Backup deleted: %(filename)s") % {"filename": filename}, "success")
            log_info_message(f"Backup deleted by '{current_user.username}': {filename}")
        else:
            flash(_("Backup file not found."), "warning")
            log_info_message(f"Backup deletion attempted but file not found: {filename}")
    except Exception as e:
        flash(_("Failed to delete backup."), "danger")
        log_error_message(f"Failed to delete backup {filename}: {e}")
    return redirect(url_for("backups.list_backups"))
