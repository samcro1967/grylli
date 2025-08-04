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
from app.utils.logging import log_debug_message, log_error_message, log_info_message


def enforce_admin_bootstrap(app):
    """
    Add before_request hook for admin bootstrap/login enforcement.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """

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
            "mfa.mfa_challenge",
            "status.health_and_version",
            "auth.rate_limit_delay",
            "meta.version_status",
            "/locale.langcheck",
            "pwa.manifest",
            "csp_report.overview",
            "assets.fonts_css",
            "assets.serve_font",
            "home.server_time",
            "tools.log_js_error",
            "meta.background_patterns",
        }

        try:
            admin_count = db.session.execute(
                text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            ).scalar()
        except Exception as e:  # pylint: disable=broad-exception-caught
            log_error_message(f"❌ Admin bootstrap check failed: {e}")
            return "Internal server error", 500

        if admin_count > 0:
            allowed_routes |= {"auth.login"}
            log_debug_message("🔓 Login route added to allowed_routes (admin exists).")

        if request.endpoint in allowed_routes:
            log_debug_message(f"✅ Allowed route: {request.endpoint}")
            return None

        if not admin_count:
            log_info_message("🚧 No admin present. Redirecting to bootstrap.")
            return redirect(url_for("auth.bootstrap"))

        if not current_user.is_authenticated:
            ip = request.remote_addr or "unknown IP"
            ua = request.user_agent.string or "unknown user-agent"
            log_info_message(f"🔒 Unauthenticated access attempt from {ip} using {ua}")
            return redirect(url_for("auth.login"))

        log_debug_message("✅ Request passed admin/login checks.")
        return None
