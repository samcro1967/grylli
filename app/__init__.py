"""
app/__init__.py
Flask application factory setup: config, DB, login, blueprints, session, i18n, and scheduler.
"""

import os
import secrets

from flask import Flask, current_app, g, redirect, request, url_for
from flask_babel import Babel
from flask_login import current_user
from flask_wtf.csrf import generate_csrf

from app.init.admin_bootstrap import enforce_admin_bootstrap
from app.init.base_url import setup_base_url
from app.init.blueprints import register_blueprints
from app.init.config import configure_app
from app.init.context_processors import register_context_processors
from app.init.database import setup_database
from app.init.errors import register_error_handlers
from app.init.i18n import setup_i18n
from app.init.login_manager import setup_login_manager
from app.init.routing import log_route_map
from app.init.scheduler import setup_scheduler
from app.init.session import configure_session
from app.init.tracing import setup_tracing
from app.middleware.remove_server_header import RemoveServerHeaderMiddleware
from app.utils.locale import get_locale
from app.utils.logging import log_exception_with_traceback, log_info_message


def create_app(config_override=None):
    """
    Flask application factory. Sets up Flask, config, DB, blueprints, Babel,
    Flask-Login, session config, and (in dev/script mode) the APScheduler.

    Args:
        config_override (dict): Optional configuration overrides for testing.

    Returns:
        Flask app instance.
    """
    base_url = os.getenv("BASE_URL", "").rstrip("/")  # default to "" if unset

    app = Flask(
        __name__,
        instance_relative_config=True,
        static_url_path=f"{base_url}/static",
        static_folder="static",
    )

    try:
        EXEMPT_ENDPOINTS = {"account.set_security_questions", "auth.logout", "static"}

        configure_app(app, config_override)
        app.config.from_object("app.config")

        # ✅ Apply DEBUG from environment explicitly (honors Docker and .env)
        app.config["DEBUG"] = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
        app.debug = app.config["DEBUG"]

        log_info_message("App configuration loaded.")

        # ✅ Inject debug flag into all templates
        @app.context_processor
        def inject_debug_flag():
            return {"debug": app.debug}

        @app.context_processor
        def inject_config():
            return dict(config=current_app.config)

        @app.after_request
        def add_cache_headers(response):
            if request.path.startswith("/static/"):
                response.headers["Cache-Control"] = "public, max-age=86400"
            return response

        @app.before_request
        def enforce_security_questions_setup():
            if (
                current_user.is_authenticated
                and not current_user.security_questions_set
                and not request.endpoint.startswith("account.set_security_questions")
                and not request.endpoint.startswith("static")
            ):
                return redirect(url_for("account.set_security_questions"))

        @app.before_request
        def generate_nonce():
            g.nonce = secrets.token_urlsafe(16)

        @app.context_processor
        def inject_nonce():
            return dict(nonce=getattr(g, "nonce", ""))

        @app.after_request
        def set_security_headers(response):
            nonce = getattr(g, "nonce", None)
            if nonce:
                frame_ancestors = "'self'" if app.debug else "'none'"
                csp_policy = (
                    f"default-src 'self'; "
                    f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
                    f"style-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com; "
                    f"font-src 'self' https://cdnjs.cloudflare.com; "
                    f"img-src 'self' data:; "
                    f"connect-src 'self' https://api.github.com; "
                    f"object-src 'none'; "
                    f"base-uri 'self'; "
                    f"form-action 'self'; "
                    f"frame-ancestors {frame_ancestors};"
                )
                response.headers["Content-Security-Policy"] = csp_policy

            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "DENY")
            return response

            @app.after_request
            def set_security_headers(response):
                nonce = getattr(g, "nonce", None)
                if nonce:
                    frame_ancestors = "'self'" if app.debug else "'none'"
                    csp_policy = (
                        f"default-src 'self'; "
                        f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
                        f"style-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com; "
                        f"font-src 'self' https://cdnjs.cloudflare.com; "
                        f"img-src 'self' data:; "
                        f"connect-src 'self' https://api.github.com; "
                        f"object-src 'none'; "
                        f"base-uri 'self'; "
                        f"form-action 'self'; "
                        f"frame-ancestors {frame_ancestors};"
                    )

                    # ✅ Enforcement header
                    response.headers["Content-Security-Policy"] = csp_policy

                    # ✅ Reporting header (add report-uri or report-to)
                    response.headers["Content-Security-Policy-Report-Only"] = (
                        csp_policy + " report-uri /grylli/meta/csp-report;"
                    )

                    # Optionally: modern `report-to` support
                    response.headers["Report-To"] = (
                        '{"group":"csp-endpoint","max_age":10886400,'
                        '"endpoints":[{"url":"https://osu.grylli:8069/grylli/meta/csp-report"}],'
                        '"include_subdomains":true}'
                    )

                # ✅ Other security headers
                response.headers.setdefault("X-Content-Type-Options", "nosniff")
                response.headers.setdefault("X-Frame-Options", "DENY")

                return response


        # Initialize Babel with locale selector
        _babel = Babel(app, locale_selector=get_locale)

        @app.context_processor
        def inject_csrf_token():
            return dict(csrf_token=generate_csrf)

        # Continue modular setup
        setup_i18n(app)
        setup_base_url(app)
        setup_database(app)
        configure_session(app)
        setup_login_manager(app)
        register_context_processors(app)
        register_blueprints(app)
        log_route_map(app)
        enforce_admin_bootstrap(app)
        setup_tracing(app)
        setup_scheduler(app)

        # Middleware
        app.wsgi_app = RemoveServerHeaderMiddleware(app.wsgi_app)
        register_error_handlers(app)

        from app.extensions import db

        app.db = db

        log_info_message("App initialized successfully.")

    except Exception as e:
        log_exception_with_traceback("App failed to initialize", e)
        raise

    return app
