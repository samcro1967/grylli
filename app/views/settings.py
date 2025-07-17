# ---------------------------------------------------------------------
# settings.py
# app/views/settings.py
# Admin settings view for Grylli (System and SMTP tabs).
# ---------------------------------------------------------------------

from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required

import app.config as project_config
from app.models import SystemConfig
from app.services.encryption import decrypt
from app.services.system_settings_email import send_email
from app.utils.logging import log_info_message, log_exception_with_traceback
from app.views.auth import admin_required

bp = Blueprint("settings_bp", __name__, url_prefix="/admin/settings")


@bp.route("/", strict_slashes=False)
@login_required
@admin_required
def settings_index():
    """
    Loads the full settings layout with tabs, defaulting to 'system' unless ?tab=... is provided.
    """
    tab = request.args.get("tab", "system")
    try:
        log_info_message(f"Access - {current_user.username} - Admin Settings (tab={tab})")

        if request.headers.get("HX-Request"):
            return render_template("admin/settings/settings_tabs.html", active_tab=tab)

        return render_template("admin/settings/settings_full.html", active_tab=tab)

    except Exception as e:
        log_exception_with_traceback("Failed to load settings index", e)
        flash(_("Failed to load settings."), "danger")
        return redirect(url_for("home.index"))


@bp.route("/system/", strict_slashes=False)
@login_required
@admin_required
def system_tab():
    """
    Serves the System tab content — returns either the full tab layout or partial only for HTMX.
    """
    try:
        log_info_message(f"Access - {current_user.username} - Settings Tab - System")

        EXCLUDED_KEYS = {"FERRET_KEY"}
        keys = [
            k for k in dir(project_config)
            if k.isupper() and not k.startswith("_") and k not in EXCLUDED_KEYS
        ]

        config_items = {}
        for key in keys:
            value = getattr(project_config, key)
            if isinstance(value, str) and "/grylli" in value:
                value = str(Path(value).as_posix())
                value = value[value.find("/grylli"):]
            config_items[key] = value

        if request.headers.get("HX-Request"):
            return render_template("admin/settings/partials/_system_settings_partial.html", config=config_items)

        return render_template("admin/settings/settings_full.html", active_tab="system", config=config_items)

    except Exception as e:
        log_exception_with_traceback("Failed to load system settings tab", e)
        return "", 204


@bp.route("/smtp/", strict_slashes=False)
@login_required
@admin_required
def smtp_tab():
    """
    Serves the SMTP tab content — returns either the full tab layout or partial only for HTMX.
    """
    try:
        log_info_message(f"Access - {current_user.username} - Settings Tab - SMTP")

        settings = SystemConfig.query.order_by(SystemConfig.key).all()
        for setting in settings:
            if setting.is_sensitive:
                try:
                    setting.value = decrypt(setting.value)
                except Exception as e:
                    setting.value = "[decryption error]"
                    log_exception_with_traceback(
                        f"Admin '{current_user.username}' failed to decrypt setting '{setting.key}'", e
                    )

        if request.headers.get("HX-Request"):
            return render_template("admin/settings/partials/_smtp_settings_partial.html", settings=settings)

        return render_template("admin/settings/settings_full.html", active_tab="smtp", settings=settings)

    except Exception as e:
        log_exception_with_traceback("Failed to load SMTP settings tab", e)
        return "", 204


@bp.route("/test-email/", methods=["POST"], strict_slashes=False)
@login_required
@admin_required
def send_test_email():
    """
    Send a test email from the SMTP settings page.
    """
    try:
        send_email(
            to=current_user.email,
            subject=_("Test Email from Grylli"),
            body=_("This is a test email from the Grylli SMTP settings page."),
        )
        log_info_message(f"Admin '{current_user.username}' sent test SMTP email.")
        flash(_("Test email sent successfully."), "success")
    except Exception as e:
        log_exception_with_traceback("Failed to send test SMTP email", e)
        flash(_("Failed to send test email: ") + str(e), "danger")

    return redirect(url_for("settings_bp.smtp_tab"))
