"""
# ---------------------------------------------------------------------
# blueprints.py
# app/init/blueprints.py
# Blueprint registration for Flask application factory.
# ---------------------------------------------------------------------
"""

import os

from flask_babel import _

from app.utils.filters import filesizeformat
from app.utils.locale import get_locale
from app.views import help as help_views
from app.views import index as index_module
from app.views import locale
from app.views.about import bp as about
from app.views.account import bp as account
from app.views.admin import bp as admin
from app.views.admin_help import admin_help
from app.views.apprise import bp as apprise
from app.views.auth import bp as auth
from app.views.backups import bp as backups
from app.views.checkin import bp as checkin
from app.views.email import bp as email
from app.views.index import bp as index
from app.views.messages import bp as messages_bp
from app.views.smtp_settings_admin import bp as smtp_settings_admin
from app.views.status import bp as status_bp
from app.views.system_info import bp as system_info
from app.views.system_settings import bp as system_settings
from app.views.user_smtp import bp as user_smtp
from app.views.users import bp as users
from app.views.webhook import bp as webhook


def register_blueprints(app):
    """
    Register all blueprints, Jinja globals, and filters.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """
    # Use the processed prefix
    prefix = app.config["URL_PREFIX"]

    # -------------------------------------------
    # Blueprint Registration (All views)
    # -------------------------------------------
    app.register_blueprint(locale.bp, url_prefix=prefix)

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
    )

    # Add Jinja globals
    app.jinja_env.globals["_"] = _
    app.jinja_env.globals["get_locale"] = get_locale
    app.jinja_env.globals["app_version"] = app.config["APP_VERSION"]

    # Register blueprints with URL prefix
    app.register_blueprint(admin, url_prefix=prefix)
    app.register_blueprint(account, url_prefix=prefix)
    app.register_blueprint(index, url_prefix=prefix)
    app.register_blueprint(auth, url_prefix=prefix)
    app.register_blueprint(about, url_prefix=prefix)
    app.register_blueprint(messages_bp, url_prefix=prefix + "/messages")
    app.register_blueprint(email, url_prefix=prefix + "/email")
    app.register_blueprint(help_views.bp, url_prefix=prefix)
    app.register_blueprint(checkin, url_prefix=prefix)
    app.register_blueprint(system_info, url_prefix=prefix)
    app.register_blueprint(users, url_prefix=prefix + "/admin/users")
    app.register_blueprint(system_settings, url_prefix=prefix + "/admin/system_settings")
    app.register_blueprint(backups, url_prefix=prefix + "/admin/backups")
    app.register_blueprint(smtp_settings_admin, url_prefix=prefix + "/admin/smtp-settings")
    app.register_blueprint(user_smtp, url_prefix=prefix + "/email/smtp")
    app.jinja_env.filters["filesizeformat"] = filesizeformat
    app.register_blueprint(admin_help, url_prefix=prefix + "/admin")

    # -------------------------------------------
    # Register Additional Blueprints
    # -------------------------------------------
    app.register_blueprint(apprise, url_prefix=prefix + "/messages/apprise")
    app.register_blueprint(webhook, url_prefix=prefix + "/messages/webhook")

    # -------------------------------------------
    # Status Endpoint
    # -------------------------------------------
    app.register_blueprint(status_bp, url_prefix=f"{prefix}/status")
