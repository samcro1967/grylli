"""
# ---------------------------------------------------------------------
# context_processors.py
# app/init/context_processors.py
# Template context processors for Flask application factory.
# ---------------------------------------------------------------------
"""

from flask_login import current_user

from app.services.settings import get_setting
from app.utils.locale import get_locale


def register_context_processors(app):
    """
    Register context processors for the app.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """

    # -------------------------------------------
    # Template Context Injection
    # -------------------------------------------
    @app.context_processor
    def inject_user():
        """Inject the current user into templates."""
        return {"current_user": current_user}

    @app.context_processor
    def inject_locale():
        """Inject locale-related functions into templates."""
        return {"get_locale": get_locale}

    @app.context_processor
    def inject_debug_mode():
        """Inject debug mode flag for template use."""
        raw_value = get_setting("DEBUG")
        debug_mode = raw_value.strip().lower() == "true"
        return {"debug_mode": debug_mode}

    @app.context_processor
    def inject_github_url():
        """Inject the GitHub repository URL into templates."""
        return {"GITHUB_URL": app.config.get("GITHUB_URL")}
