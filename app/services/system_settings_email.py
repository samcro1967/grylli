"""
# ---------------------------------------------------------------------
# system_settings_email.py
# app/services/system_settings_email.py
# Utility for sending emails using system settings.
# ---------------------------------------------------------------------
"""

import smtplib
from email.mime.text import MIMEText

from flask import current_app
from flask_babel import _  # ✅ i18n support

# ------------------------ Imports (PEP8 order) -----------------------
from app.models import SystemConfig
from app.services.encryption import decrypt
from app.utils.logging import log_error_message, log_info_message


# ---------------------------------------------------------------------
# get_setting
# ---------------------------------------------------------------------
def get_setting(key, decrypt_value=False):
    """
    Retrieves a system configuration setting value.

    Args:
        key: Name of the configuration setting to retrieve.
        decrypt_value: Whether to decrypt the value before returning it.

    Returns:
        The value of the configuration setting.

    Raises:
        ValueError: If the configuration setting does not exist or decryption fails.
    """
    setting = SystemConfig.query.filter_by(key=key).first()
    if not setting:
        raise ValueError(_("Missing required config setting: ") + key)

    if decrypt_value and setting.is_sensitive:
        try:
            value = decrypt(setting.value)
        except Exception as e:
            raise ValueError(
                _("Failed to decrypt %(key)s: %(error)s") % {"key": key, "error": str(e)}
            )
    else:
        value = setting.value

    clean_value = value.strip()
    log_info_message("Reached before return")  # ← debug check
    return clean_value


# ---------------------------------------------------------------------
# send_email
# ---------------------------------------------------------------------
def send_email(to, subject, body):
    """
    Send an email using system SMTP settings.

    Args:
        to: Recipient email address.
        subject: Email subject.
        body: Email message body.

    Raises:
        Exception if sending fails or configuration is missing.
    """
    log_info_message("Preparing email to %(to)s" % {"to": to})

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = get_setting("EMAIL_FROM")
    msg["To"] = to

    smtp_host = get_setting("SMTP_HOST")
    smtp_port = int(get_setting("SMTP_PORT"))
    smtp_user = get_setting("SMTP_USER")

    try:
        smtp_pass = get_setting("SMTP_PASS", decrypt_value=True)
    except Exception as e:
        log_error_message("[DEBUG] SMTP_PASS decryption failed.")
        log_error_message(f"[DEBUG] Exception: {e}")
        raise

    use_tls = get_setting("SMTP_USE_TLS") == "1"

    log_info_message(
        "SMTP host = '%(host)s', port = %(port)s" % {"host": smtp_host, "port": smtp_port}
    )
    log_info_message("Using user: %(user)s" % {"user": smtp_user})

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                log_info_message("Starting TLS")
                server.starttls()
            log_info_message("Logging in")
            server.login(smtp_user, smtp_pass)
            log_info_message("Sending message")
            server.send_message(msg)
        log_info_message("Email sent successfully")
    except Exception as e:
        log_error_message("SMTP error: " + str(e))
        raise


# ---------------------------------------------------------------------
# End of file: app/services/system_settings_email.py
# ---------------------------------------------------------------------
