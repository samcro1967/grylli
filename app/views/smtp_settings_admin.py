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
from app.utils.logging import log_error_message
from app.views.auth import admin_required

bp = Blueprint("smtp_settings_admin", __name__)


@bp.route("/")
@login_required
@admin_required
def view_smtp_config():
    settings = SystemConfig.query.order_by(SystemConfig.key).all()
    for setting in settings:
        if setting.is_sensitive:
            try:
                setting.value = decrypt(setting.value)
            except Exception:
                setting.value = "[decryption error]"
    return render_template("admin/smtp_config.html", settings=settings)


@bp.route("/test-email/", methods=["POST"])
@login_required
@admin_required
def send_test_email():
    if current_user.role != "admin":
        return "Unauthorized", 403

    try:
        send_email(
            to=current_user.email,
            subject=_("Test Email from Grylli"),
            body=_("This is a test email from the Grylli SMTP settings page."),
        )
        flash(_("Test email sent successfully."), "success")
    except Exception as e:
        flash(_("Failed to send test email: ") + str(e), "danger")
        log_error_message("Test email failed: " + str(e))

    # << FIXED: use new blueprint and view name
    return redirect(url_for("smtp_settings_admin.view_smtp_config"))
