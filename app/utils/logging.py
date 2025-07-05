"""
# ---------------------------------------------------------------------
# logging.py
# app/utils/logging.py
# Centralized logging helpers for Grylli.
# ---------------------------------------------------------------------
"""

import logging
import sys
from datetime import datetime

from flask import has_app_context

from app.config import LOG_FILE_PATH

# ---------------------------------------------------------------------
# Configuration: ANSI color codes for terminal output
# ---------------------------------------------------------------------
COLOR_RESET = "\033[0m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_RED = "\033[91m"


# ---------------------------------------------------------------------
# _timestamp
# ---------------------------------------------------------------------
def _timestamp():
    """
    Returns the current timestamp in standard log format.

    Returns:
        str: Timestamp string (e.g., '2025-05-15 07:45:22')
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------
# log_info_message
# ---------------------------------------------------------------------
def log_info_message(message: str):
    """
    Logs a blue INFO-level message to stdout.
    """
    print(
        f"{COLOR_BLUE}{_timestamp()} - INFO - {message}{COLOR_RESET}", file=sys.stdout, flush=True
    )
    logging.info(message)


# ---------------------------------------------------------------------
# log_debug_message
# ---------------------------------------------------------------------
def log_debug_message(message: str):
    """
    Logs a cyan DEBUG-level message to stdout if DEBUG = True in system_config.
    """
    try:
        if not has_app_context():
            return

        from app.models import SystemConfig

        row = SystemConfig.query.filter_by(key="DEBUG").first()
        if row and str(row.value).strip().lower() in ["1", "true", "yes"]:
            print(
                f"{COLOR_CYAN}{_timestamp()} - DEBUG - {message}{COLOR_RESET}",
                file=sys.stdout,
                flush=True,
            )
            logging.debug(message)
    except Exception:
        pass


# ---------------------------------------------------------------------
# log_error_message
# ---------------------------------------------------------------------
def log_error_message(message: str):
    """
    Logs a red ERROR-level message to stderr.

    Args:
        message (str): The error message to log.
    """
    print(
        f"{COLOR_RED}{_timestamp()} - ERROR - {message}{COLOR_RESET}", file=sys.stderr, flush=True
    )
    logging.error(message)


# ---------------------------------------------------------------------
# log_step
# ---------------------------------------------------------------------
def log_step(title: str):
    """
    Logs a visual separator to highlight a major step in execution.

    Args:
        title (str): A short label for the step (e.g., 'Initializing App').
    """
    print(f"\n{COLOR_BLUE}{'-' * 60}\n{title.upper()}\n{'-' * 60}{COLOR_RESET}")


# ---------------------------------------------------------------------
# log_exception_with_traceback
# ---------------------------------------------------------------------
def log_exception_with_traceback(prefix: str, exception: Exception):
    """
    Logs an error message and optional traceback if DEBUG = True in system_config.

    Args:
        prefix (str): A short explanation of what failed.
        exception (Exception): The exception that was caught.
    """
    full_message = f"{prefix}: {str(exception)}"
    log_error_message(full_message)
    logging.exception(full_message)  # includes traceback

    if has_app_context():
        from app.models import SystemConfig

        row = SystemConfig.query.filter_by(key="DEBUG").first()
        if row and str(row.value).strip().lower() in ["1", "true", "yes"]:
            import traceback

            traceback.print_exc()
