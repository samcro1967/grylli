"""
# ---------------------------------------------------------------------
# login_manager.py
# app/init/login_manager.py
# Flask-Login setup for Flask application factory.
# ---------------------------------------------------------------------
"""

from flask_login import LoginManager

from app.extensions import db, login_manager
from app.models import User
from app.utils.logging import log_debug_message


def setup_login_manager(app):
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        log_debug_message(
            f"[login_manager] Loaded user ID {user_id}: {user.username if user else 'None'}"
        )
        return user

    @login_manager.unauthorized_handler
    def handle_unauthorized():
        from flask import request, redirect, url_for
        ip = request.remote_addr or "unknown IP"
        ua = request.user_agent.string or "unknown user-agent"
        log_info_message(f"🔒 Unauthenticated access attempt from {ip} using {ua}")
        return redirect(url_for("auth.login"))
