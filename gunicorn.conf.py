"""
gunicorn_conf.py
Gunicorn configuration for Grylli
"""

# pylint: disable=invalid-name, import-outside-toplevel

import os
import logging
from logging.handlers import RotatingFileHandler
from app.config import LOG_FILE_PATH
from app.utils.banner import print_banner_and_github
from app.utils.logging import log_step, log_info_message

# Ensure log directory exists
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

BIND = f"0.0.0.0:{os.getenv('FLASK_APP_PORT', '5069')}"
RELOAD = False
LOGLEVEL = "debug" if DEBUG else "info"
ACCESSLOG = None
ERRORLOG = "-"
CAPTURE_OUTPUT = True
preload_app = True
WORKERS = 1

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
    from app import create_app
    app = create_app()
    print_banner_and_github(app)
    log_step("Starting Grylli")

def post_fork(_server, _worker):
    """
    Attach file logger and start scheduler after worker fork.
    """
    print("✅ post_fork reached")  # TEMP: confirm this executes
    file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10_000_000, backupCount=7)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))

    root_logger = logging.getLogger()
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        root_logger.addHandler(file_handler)
        root_logger.propagate = False

    from app import create_app
    from app.services.scheduler.scheduler_job import start_scheduler

    app = create_app()
    start_scheduler(app)
    log_info_message("✅ APScheduler started in post_fork")
