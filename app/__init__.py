"""
app/__init__.py
Flask application factory setup: config, DB, login, blueprints, session, i18n, and scheduler.
"""

from flask import Flask
from flask_babel import Babel

from app.init.admin_bootstrap import enforce_admin_bootstrap
from app.init.base_url import setup_base_url
from app.init.blueprints import register_blueprints
from app.init.config import configure_app
from app.init.context_processors import register_context_processors
from app.init.database import setup_database
from app.init.i18n import setup_i18n
from app.init.login_manager import setup_login_manager
from app.init.routing import log_route_map
from app.init.scheduler import setup_scheduler
from app.init.session import configure_session
from app.init.tracing import setup_tracing
from app.utils.locale import get_locale


def create_app(config_override=None):
    """
    Flask application factory. Sets up Flask, config, DB, blueprints, Babel,
    Flask-Login, session config, and (in dev/script mode) the APScheduler.

    Args:
        config_override (dict): Optional configuration overrides for testing.

    Returns:
        Flask app instance.
    """
    app = Flask(__name__, instance_relative_config=True)
    configure_app(app, config_override)

    # Always load config the same way, no matter who calls us!
    app.config.from_object("app.config")
    app.debug = app.config.get("DEBUG", False)

    # Initialize Babel with the locale_selector function
    _babel = Babel(app, locale_selector=get_locale)

    # Continue with modular setup
    setup_i18n(app)  # still sets config options for Babel
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
    return app
