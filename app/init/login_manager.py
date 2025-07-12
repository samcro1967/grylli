"""
# ---------------------------------------------------------------------
# login_manager.py
# app/init/login_manager.py
# Flask-Login setup for Flask application factory.
# ---------------------------------------------------------------------
"""

from flask_login import LoginManager

from app.extensions import db
from app.models import User
from app.utils.logging import log_debug_message


def setup_login_manager(app):
    """
    Setup Flask-Login for the app.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """
    # -------------------------------------------
    # Flask-Login Setup
    # -------------------------------------------
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by user ID (Flask-Login requirement)."""
        user = db.session.get(User, int(user_id))
        log_debug_message(
            f"[login_manager] Loaded user ID {user_id}: {user.username if user else 'None'}"
        )
        return user
