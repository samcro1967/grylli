# ---------------------------------------------------------------------
# login_manager.py
# app/init/login_manager.py
# Flask-Login setup for Flask application factory.
# ---------------------------------------------------------------------

from flask import request, redirect, url_for
from flask_login import LoginManager
from urllib.parse import urlparse

from app.extensions import db, login_manager
from app.models import User
from app.utils.logging import log_debug_message, log_info_message


def setup_login_manager(app):
    # Ensure the blueprint-qualified login endpoint
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
        ip = request.remote_addr or "unknown IP"
        ua = request.user_agent.string or "unknown user-agent"
        log_info_message(f"🔒 Unauthenticated access attempt from {ip} using {ua}")

        # Convert absolute URL → safe relative path
        parsed = urlparse(request.url)
        rel_path = parsed.path + (("?" + parsed.query) if parsed.query else "")

        return redirect(url_for("auth.login", next=rel_path))

    # Optional: return for tests or debugging; harmless if unused
    return login_manager
