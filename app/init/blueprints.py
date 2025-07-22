"""
# ---------------------------------------------------------------------
# blueprints.py
# app/init/blueprints.py
# Blueprint registration for Flask application factory.
# ---------------------------------------------------------------------
"""

import os
import pprint

from flask_babel import _

from app.utils.filters import filesizeformat
from app.utils.locale import get_locale
from app.utils.logging import log_info_message
from app.views import help as help_views
from app.views import index as index_module
from app.views import locale, privacy
from app.views.about import bp as about
from app.views.account import bp as account
from app.views.admin import bp as admin
from app.views.admin_help import admin_help
from app.views.apprise import bp as apprise
from app.views.auth import bp as auth
from app.views.checkin import bp as checkin
from app.views.csp_report import bp as csp_report
from app.views.debug import bp as debug_bp
from app.views.email import bp as email
from app.views.index import bp as index
from app.views.messages import bp as messages_bp
from app.views.meta import bp as meta
from app.views.mfa import bp as mfa_bp
from app.views.pwa import bp as pwa
from app.views.reminders import bp as reminders_bp
from app.views.reports import bp as reports
from app.views.status import bp as status_bp
from app.views.system_info import bp as system_info
from app.views.user_smtp import bp as user_smtp
from app.views.users import bp as users
from app.views.webhook import bp as webhook
from app.views.settings import bp as settings_bp
from app.views.tools import bp as tools
from app.views.assets import bp as assets

def register_blueprints(app):
    """
    Register all blueprints, Jinja globals, and filters.
    DO NOT CHANGE FUNCTIONALITY OR ORDER—direct copy from create_app.
    """
    prefix = app.config["URL_PREFIX"].rstrip("/")
    log_info_message(f"🌐 Registering blueprints with URL prefix: '{prefix}'")

    # -------------------------------
    # Core Session Config & Globals
    # -------------------------------
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
    )
    app.jinja_env.globals["_"] = _
    app.jinja_env.globals["get_locale"] = get_locale
    app.jinja_env.globals["app_version"] = app.config["APP_VERSION"]
    app.jinja_env.filters["filesizeformat"] = filesizeformat

    # -------------------------------
    # Register All Blueprints
    # -------------------------------
    def _r(bp, path):
        app.register_blueprint(bp, url_prefix=path)
        log_info_message(f"🧩 Registered blueprint at '{path}'")

    _r(locale.bp, prefix)
    _r(admin, prefix)
    _r(account, prefix)
    _r(index, prefix)
    _r(auth, prefix)
    _r(about, prefix)
    _r(messages_bp, f"{prefix}/messages")
    _r(email, f"{prefix}/email")
    _r(help_views.bp, prefix)
    _r(checkin, prefix)
    _r(system_info, prefix)
    _r(users, f"{prefix}/admin/users")
    _r(settings_bp, f"{prefix}/admin/settings")
    _r(user_smtp, f"{prefix}/email/smtp")
    _r(admin_help, f"{prefix}/admin")
    _r(reminders_bp, f"{prefix}/reminders")
    _r(mfa_bp, f"{prefix}/mfa")
    _r(privacy.bp, f"{prefix}/privacy")
    _r(apprise, f"{prefix}/messages/apprise")
    _r(webhook, f"{prefix}/messages/webhook")
    _r(status_bp, f"{prefix}/status")
    _r(meta, f"{prefix}/meta")
    _r(pwa, f"{prefix}/pwa")
    _r(csp_report, f"{prefix}/csp-report")
    _r(reports, f"{prefix}/admin/reports")
    _r(tools, f"{prefix}/admin/tools")
    _r(assets, f"{prefix}/assets")

    # -------------------------------
    # Conditionally register debug blueprint
    # -------------------------------
    if os.environ.get("DEBUG", "").lower() in ("true", "1"):
        _r(debug_bp, f"{prefix}/debug")
        # Register the pprint filter for debug templates
        app.jinja_env.filters["pprint"] = lambda v: pprint.pformat(v)
        log_info_message("🪲 Debug blueprint registered at '{}/debug'".format(prefix))

    log_info_message("✅ All blueprints registered successfully.")
