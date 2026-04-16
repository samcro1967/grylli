"""
setup_logging.py
Sets up file-based log rotation for Grylli at app startup.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from app.config import LOG_FILE_PATH


def configure_file_logging():
    log = logging.getLogger()

    # Only configure ONCE per process
    if getattr(log, "_grylli_configured", False):
        return

    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=10_000_000,
        backupCount=7
    )

    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    log.propagate = False

    # 🔒 Mark as configured
    log._grylli_configured = True
