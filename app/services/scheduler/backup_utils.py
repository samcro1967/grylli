# ---------------------------------------------------------------------
# backup_utils.py
# app/services/scheduler/backup_utils.py
# Utility functions to create, list, and clean up DB backups
# ---------------------------------------------------------------------

import os
import shutil
from datetime import datetime, timedelta

from flask import current_app

from app.utils.logging import log_error_message, log_info_message


# ---------------------------------------------------------------------
# create_backup
# ---------------------------------------------------------------------
def create_backup():
    """
    Creates a timestamped backup of the application's SQLite database.

    Returns:
        The full file path of the newly created backup, or None on failure.
    """
    try:
        src = current_app.config["DATABASE_PATH"]
        dest_dir = current_app.config["BACKUP_DIR"]
        os.makedirs(dest_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest_file = os.path.join(dest_dir, f"grylli-backup-{timestamp}.db")

        shutil.copy2(src, dest_file)
        log_info_message(f"Scheduler [CreateBackup] - Success - Backup created at: {dest_file}")
        return dest_file
    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [CreateBackup] - Failure - Failed to create database backup: {e}"
        )
        return None


# ---------------------------------------------------------------------
# get_backup_files
# ---------------------------------------------------------------------
def get_backup_files():
    """
    Lists all backup files in the backup directory, sorted newest first.

    Returns:
        A list of filenames (not full paths), sorted reverse chronologically.
    """
    try:
        dir_path = current_app.config["BACKUP_DIR"]
        os.makedirs(dir_path, exist_ok=True)

        files = [
            f for f in os.listdir(dir_path) if f.startswith("grylli-backup-") and f.endswith(".db")
        ]
        sorted_files = sorted(files, reverse=True)
        log_info_message(
            f"Scheduler [GetBackupFiles] - Success - Found {len(sorted_files)} backup file(s)."
        )
        return sorted_files
    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [GetBackupFiles] - Failure - Failed to list backup files: {e}"
        )
        return []


# ---------------------------------------------------------------------
# delete_old_backups
# ---------------------------------------------------------------------
def delete_old_backups(days_to_keep=7):
    """
    Deletes backup files older than the specified number of days.

    Args:
        days_to_keep: Number of days to retain backups (default: 7).
    """
    try:
        dir_path = current_app.config["BACKUP_DIR"]
        if not os.path.exists(dir_path):
            log_info_message(
                "Scheduler [DeleteOldBackups] - Success - Backup directory does not exist. Skipping deletion."
            )
            return

        now = datetime.now()
        deleted_count = 0

        for f in os.listdir(dir_path):
            if not f.startswith("grylli-backup-") or not f.endswith(".db"):
                continue

            path = os.path.join(dir_path, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if (now - mtime).days > days_to_keep:
                    os.remove(path)
                    log_info_message(
                        f"Scheduler [DeleteOldBackups] - Success - Deleted old backup: {f}"
                    )
                    deleted_count += 1
            except Exception as e:
                log_error_message(
                    f"ERROR - Scheduler [DeleteOldBackups] - Failure - Failed to delete backup {f}: {e}"
                )
                continue

        log_info_message(
            f"Scheduler [DeleteOldBackups] - Success - Cleanup complete. Deleted {deleted_count} old backup(s)."
        )

    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [DeleteOldBackups] - Failure - Unexpected error during backup cleanup: {e}"
        )
