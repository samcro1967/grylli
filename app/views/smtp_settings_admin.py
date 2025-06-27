# ---------------------------------------------------------------------
# smtp_settings_admin.py
# app/views/smtp_settings_admin.py
# Admin SMTP configuration and email test views for Grylli.
# ---------------------------------------------------------------------

from flask import Blueprint, flash, redirect, render_template, url_for, request
from flask_babel import _
from flask_login import current_user, login_required

from app.models import SystemConfig
from app.services.encryption import decrypt
from app.services.system_settings_email import send_email
from app.utils.logging import (
    log_error_message,
    log_exception_with_traceback,
    log_info_message,
)
from app.views.auth import admin_required

bp = Blueprint("smtp_settings_admin", __name__)


# ---------------------------------------------------------------------
# View: View SMTP Config
# ---------------------------------------------------------------------
@bp.route("/")
@login_required
@admin_required
def view_smtp_config():
    """
    Display the decrypted system SMTP configuration to an admin user.
    Returns a partial if requested via HTMX.
    """
    try:
        settings = SystemConfig.query.order_by(SystemConfig.key).all()
        for setting in settings:
            if setting.is_sensitive:
                try:
                    setting.value = decrypt(setting.value)
                except Exception as e:
                    setting.value = "[decryption error]"
                    log_exception_with_traceback(f"Failed to decrypt setting '{setting.key}'", e)

        log_info_message(f"Admin user '{current_user.username}' viewed system SMTP settings.")

        if request.headers.get("HX-Request"):
            return render_template("admin/smtp_config_partial.html", settings=settings)
        return render_template("admin/smtp_config_full.html", settings=settings)

    except Exception as e:
        log_exception_with_traceback("Error loading SMTP config settings", e)
        flash(_("Failed to load SMTP settings."), "danger")
        return redirect(url_for("home.index"))


# ---------------------------------------------------------------------
# View: Test SMTP Config
# ---------------------------------------------------------------------
@bp.route("/test-email/", methods=["POST"])
@login_required
@admin_required
def send_test_email():
    """
    Send a test email using the system SMTP configuration.
    """
    if current_user.role != "admin":
        return "Unauthorized", 403

    try:
        send_email(
            to=current_user.email,
            subject=_("Test Email from Grylli"),
            body=_("This is a test email from the Grylli SMTP settings page."),
        )
        log_info_message(
            f"Admin user '{current_user.username}' sent a test email from system SMTP settings."
        )
        flash(_("Test email sent successfully."), "success")
    except Exception as e:
        log_exception_with_traceback("Failed to send test SMTP email", e)
        flash(_("Failed to send test email: ") + str(e), "danger")

    return redirect(url_for("smtp_settings_admin.view_smtp_config"))
