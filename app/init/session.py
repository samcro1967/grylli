"""
# ---------------------------------------------------------------------
# session.py
# app/init/session.py
# Session Configuration for Flask application factory.
# ---------------------------------------------------------------------
"""

from datetime import timedelta


def configure_session(app):
    """
    Configure session settings for Flask app.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """
    # -------------------------------------------
    # Session Configuration
    # -------------------------------------------
    app.config["SESSION_PERMANENT"] = True
    app.permanent_session_lifetime = timedelta(days=30)
