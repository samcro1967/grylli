"""
# ---------------------------------------------------------------------
# scheduler.py
# app/init/scheduler.py
# Scheduler setup for Flask application factory.
# ---------------------------------------------------------------------
"""

import os

from flask import has_request_context

from app.services.scheduler.scheduler_job import start_scheduler
from app.utils.logging import log_info_message


def setup_scheduler(app):
    """
    Setup APScheduler for the app if appropriate.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """
    # -------------------------------------------
    # Scheduler Setup (only dev/script, not Gunicorn)
    # -------------------------------------------
    is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "").lower()
    is_werkzeug_main = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    in_direct_script = (
        not has_request_context()
    )  # True if running via python run.py, not via Flask CLI

    if (is_werkzeug_main or in_direct_script) and not is_gunicorn:
        start_scheduler(app)
        log_info_message("✅ Scheduler started from Flask dev server or direct script.")
    elif is_gunicorn:
        log_info_message("ℹ️ Skipping scheduler — handled by Gunicorn post_fork.")
    else:
        log_info_message("ℹ️ Scheduler not started in this context.")
