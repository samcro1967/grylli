"""
# ---------------------------------------------------------------------
# backup_utils.py
# app/services/scheduler/backup_utils.py
# Utility functions to create, list, and clean up DB backups
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
import os
import shutil
from datetime import datetime, timedelta

from flask import current_app


# ---------------------------------------------------------------------
# create_backup
# ---------------------------------------------------------------------
def create_backup():
    """
    Creates a timestamped backup of the application's SQLite database.

    Returns:
        The full file path of the newly created backup.

    Notes:
        - The backup directory is created if it does not exist.
        - Uses 'shutil.copy2' to preserve metadata.
    """
    src = current_app.config["DATABASE_PATH"]
    dest_dir = current_app.config["BACKUP_DIR"]
    os.makedirs(dest_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest_file = os.path.join(dest_dir, f"grylli-backup-{timestamp}.db")
    shutil.copy2(src, dest_file)
    return dest_file


# ---------------------------------------------------------------------
# get_backup_files
# ---------------------------------------------------------------------
def get_backup_files():
    """
    Lists all backup files in the backup directory, sorted newest first.

    Returns:
        A list of filenames (not full paths), sorted reverse chronologically.

    Notes:
        - Ensures the backup directory exists before listing.
        - Filters files to match backup filename pattern.
    """
    dir_path = current_app.config["BACKUP_DIR"]
    os.makedirs(dir_path, exist_ok=True)
    files = [
        f for f in os.listdir(dir_path) if f.startswith("grylli-backup-") and f.endswith(".db")
    ]
    return sorted(files, reverse=True)


# ---------------------------------------------------------------------
# delete_old_backups
# ---------------------------------------------------------------------
def delete_old_backups(days_to_keep=7):
    """
    Deletes backup files older than the specified number of days.

    Args:
        days_to_keep: Number of days to retain backups (default: 7).

    Notes:
        - Skips non-backup files.
        - Ignores and continues on errors (e.g., file in use).
    """
    dir_path = current_app.config["BACKUP_DIR"]
    if not os.path.exists(dir_path):
        return
    now = datetime.now()
    for f in os.listdir(dir_path):
        if not f.startswith("grylli-backup-") or not f.endswith(".db"):
            continue
        path = os.path.join(dir_path, f)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if (now - mtime).days > days_to_keep:
                os.remove(path)
        except Exception:
            # Silently skip errors to avoid breaking the cleanup routine
            continue
