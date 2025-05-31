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
    try:
        backup_path = create_backup()
        flash(
            _("Backup created: %(filename)s") % {"filename": os.path.basename(backup_path)},
            "success",
        )
        log_info_message(f"Backup created: {backup_path}")
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
    path = os.path.join(current_app.config["BACKUP_DIR"], filename)
    try:
        if os.path.exists(path):
            os.remove(path)
            flash(_("Backup deleted: %(filename)s") % {"filename": filename}, "success")
            log_info_message(f"Backup deleted: {filename}")
        else:
            flash(_("Backup file not found."), "warning")
    except Exception as e:
        flash(_("Failed to delete backup."), "danger")
        log_error_message(f"Failed to delete backup {filename}: {e}")
    return redirect(url_for("backups.list_backups"))
