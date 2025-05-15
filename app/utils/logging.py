# ---------------------------------------------------------------------
# logging.py
# Centralized logging helpers for Grylli
# ---------------------------------------------------------------------

import logging
import sys
from datetime import datetime

# ---------------------------------------------------------------------
# Configuration: ANSI color codes for terminal output
# ---------------------------------------------------------------------

COLOR_RESET = "\033[0m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_RED = "\033[91m"

# ---------------------------------------------------------------------
# Log level constants
# ---------------------------------------------------------------------

INFO = "INFO"
DEBUG = "DEBUG"
ERROR = "ERROR"

# ---------------------------------------------------------------------
# Global log level
# TODO: Replace with config/env override
# ---------------------------------------------------------------------

LOG_LEVEL = DEBUG

# ---------------------------------------------------------------------
# Internal helper: Timestamp formatter
# ---------------------------------------------------------------------

def _timestamp():
    """
    Returns the current timestamp in standard log format.
    Returns:
        str: Timestamp string (e.g., '2025-05-15 07:45:22')
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------------------------------------------------------------------
# Public Logging Functions
# ---------------------------------------------------------------------

def log_info_message(message: str):
    """
    Logs a blue INFO-level message to stdout if LOG_LEVEL is INFO or DEBUG.
    Args:
        message (str): The message to log.
    """
    if LOG_LEVEL in [INFO, DEBUG]:
        print(f"{COLOR_BLUE}{_timestamp()} - INFO - {message}{COLOR_RESET}", file=sys.stdout)
# ---------------------------------------------------------------------
def log_debug_message(message: str):
    """
    Logs a cyan DEBUG-level message to stdout if LOG_LEVEL is DEBUG.
    Args:
        message (str): The message to log.
    """
    if LOG_LEVEL == DEBUG:
        print(f"{COLOR_CYAN}{_timestamp()} - DEBUG - {message}{COLOR_RESET}", file=sys.stdout)
# ---------------------------------------------------------------------
def log_error_message(message: str):
    """
    Logs a red ERROR-level message to stderr.
    Args:
        message (str): The error message to log.
    """
    print(f"{COLOR_RED}{_timestamp()} - ERROR - {message}{COLOR_RESET}", file=sys.stderr)
# ---------------------------------------------------------------------
def log_step(title: str):
    """
    Logs a visual separator to highlight a major step in execution.
    Args:
        title (str): A short label for the step (e.g., 'Initializing App').
    """
    print(f"\n{COLOR_BLUE}{'-' * 60}\n{title.upper()}\n{'-' * 60}{COLOR_RESET}")
# ---------------------------------------------------------------------
def log_exception_with_traceback(prefix: str, exception: Exception):
    """
    Logs an error message and optional traceback if in DEBUG mode.
    Args:
        prefix (str): A short explanation of what failed.
        exception (Exception): The exception that was caught.
    """
    log_error_message(f"{prefix}: {str(exception)}")

    # If debugging, print full traceback
    if LOG_LEVEL == DEBUG:
        import traceback
        traceback.print_exc()
