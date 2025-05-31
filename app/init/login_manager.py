"""
# ---------------------------------------------------------------------
# login_manager.py
# app/init/login_manager.py
# Flask-Login setup for Flask application factory.
# ---------------------------------------------------------------------
"""

from flask_login import LoginManager

from app.models import User


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
        return User.query.get(int(user_id))
