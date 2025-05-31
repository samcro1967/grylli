"""
# ---------------------------------------------------------------------
# admin_bootstrap.py
# app/init/admin_bootstrap.py
# Admin bootstrap & login enforcement for Flask application factory.
# ---------------------------------------------------------------------
"""

from flask import redirect, request, url_for
from flask_login import current_user
from sqlalchemy import text

from app.extensions import db
from app.utils.logging import log_debug_message, log_error_message


def enforce_admin_bootstrap(app):
    """
    Add before_request hook for admin bootstrap/login enforcement.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """

    # -------------------------------------------
    # Admin Bootstrap & Login Enforcement
    # -------------------------------------------
    @app.before_request
    def enforce_login_and_bootstrap():
        """Check admin presence and enforce login for secure routes."""
        log_debug_message(f"🧭 REQUEST PATH: {request.path}")
        log_debug_message(f"🧭 REQUEST ENDPOINT: {request.endpoint}")

        allowed_routes = {
            "auth.bootstrap",
            "auth.forgot_username",
            "auth.forgot_password",
            "auth.reset_password",
            "auth.signup",
            "auth.activate_account",
            "static",
            "checkin.handle_checkin",
            "locale.set_locale_post",
            "locale.set_language",
            "admin_help.help_page",
        }

        try:
            admin_count = db.session.execute(
                text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            ).scalar()
        except Exception as e:  # pylint: disable=broad-exception-caught
            log_error_message(f"Admin bootstrap check failed: {e}")
            return "Internal server error", 500

        # If at least one admin exists, add login page to allowed routes
        if admin_count > 0:
            allowed_routes = set(allowed_routes) | {"auth.login"}

        if request.endpoint in allowed_routes:
            return None

        # If no admin, force everything to bootstrap except allowed_routes
        if not admin_count:
            return redirect(url_for("auth.bootstrap"))

        # If not logged in, force login
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        return None
