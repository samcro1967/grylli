"""
gunicorn_conf.py
Gunicorn configuration for Grylli
"""

# pylint: disable=invalid-name, import-outside-toplevel

import os
from app.utils.banner import print_banner_and_github
from app.utils.logging import log_step, log_info_message

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

BIND = f"0.0.0.0:{os.getenv('FLASK_APP_PORT', '5069')}"
RELOAD = False
LOGLEVEL = "debug" if DEBUG else "info"
ACCESSLOG = None
ERRORLOG = "-"
CAPTURE_OUTPUT = True
WORKERS = 1

# Gunicorn expects lowercase names
bind = BIND
reload = RELOAD
loglevel = LOGLEVEL
accesslog = ACCESSLOG
errorlog = ERRORLOG
capture_output = CAPTURE_OUTPUT
workers = WORKERS

def when_ready(_server):
    """
    Print banner and log when Gunicorn master is ready.
    """
    from app import create_app  # Gunicorn best practice for config files
    app = create_app()
    print_banner_and_github(app)
    log_step("Starting Grylli")

def post_fork(_server, _worker):
    """
    Start background scheduler after Gunicorn worker fork.
    """
    from app import create_app
    from app.services.scheduler.scheduler_job import start_scheduler

    app = create_app()
    start_scheduler(app)
    log_info_message("✅ APScheduler started in post_fork")
