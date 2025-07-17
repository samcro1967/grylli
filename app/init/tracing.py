"""
# ---------------------------------------------------------------------
# tracing.py
# app/init/tracing.py
# Debug request tracing for Flask application factory.
# ---------------------------------------------------------------------
"""

from flask import request

from app.utils.logging import log_debug_message


def setup_tracing(app):
    """
    Register debug-mode request tracing if app.debug is True.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """
    if app.debug:

        @app.before_request
        def trace_request():
            """Log details of incoming requests (debug mode only)."""
            log_debug_message(
                f"[TRACE] Incoming path: {request.path} → endpoint: {request.endpoint}"
            )
