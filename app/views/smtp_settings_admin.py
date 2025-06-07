"""
# ---------------------------------------------------------------------
# smtp_settings_admin.py
# app/views/smtp_settings_admin.py
# Admin SMTP configuration and email test views for Grylli.
# ---------------------------------------------------------------------
"""

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.models import SystemConfig
from app.services.encryption import decrypt
from app.services.system_settings_email import send_email
from app.utils.logging import log_error_message, log_info_message
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
    View the SMTP configuration settings for the system.

    This view fetches all system configuration settings from the database,
    decrypts any sensitive values, and renders them in the SMTP configuration
    template. Only accessible to authenticated admin users.

    Returns:
        A rendered template displaying the system SMTP configuration settings.
    """

    settings = SystemConfig.query.order_by(SystemConfig.key).all()
    for setting in settings:
        if setting.is_sensitive:
            try:
                setting.value = decrypt(setting.value)
            except Exception:
                setting.value = "[decryption error]"
    log_info_message(f"Admin user '{current_user.username}' viewed system SMTP settings.")
    return render_template("admin/smtp_config.html", settings=settings)


# ---------------------------------------------------------------------
# View: Test SMTP Config
# ---------------------------------------------------------------------
@bp.route("/test-email/", methods=["POST"])
@login_required
@admin_required
def send_test_email():
    """
    Sends a test email from the system SMTP settings page.

    This function is accessible only to authenticated admin users. It attempts
    to send a test email to the current user's email address using the system's
    SMTP settings. If the email is sent successfully, a success message is
    flashed. In case of failure, an error message is flashed and logged.

    Returns:
        A redirect to the SMTP configuration view on success or failure.
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
        flash(_("Failed to send test email: ") + str(e), "danger")
        log_error_message("Test email failed: " + str(e))

    # << FIXED: use new blueprint and view name
    return redirect(url_for("smtp_settings_admin.view_smtp_config"))
