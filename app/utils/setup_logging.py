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
    if not any(isinstance(h, RotatingFileHandler) for h in log.handlers):
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10_000_000, backupCount=7)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        log.setLevel(logging.DEBUG)
        log.addHandler(file_handler)
        log.propagate = False
