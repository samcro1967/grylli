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
from flask_babel import _

from app.models import SystemConfig
from app.services.encryption import decrypt
from app.utils.logging import log_error_message, log_exception_with_traceback, log_info_message


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
    try:
        setting = SystemConfig.query.filter_by(key=key).first()
    except Exception as e:
        log_error_message(f"[system_email] DB error retrieving key '{key}': {e}")
        raise ValueError(_("Error loading config key: ") + key)

    if not setting:
        log_error_message(f"[system_email] Missing config key: {key}")
        raise ValueError(_("Missing required config setting: ") + key)

    raw_value = setting.value

    if decrypt_value and setting.is_sensitive:
        try:
            value = decrypt(raw_value)
            log_info_message(f"[system_email] Decrypted setting: {key}")
        except Exception as e:
            log_error_message(f"[system_email] Failed to decrypt {key}: {e}")
            raise ValueError(
                _("Failed to decrypt %(key)s: %(error)s") % {"key": key, "error": str(e)}
            )
    else:
        value = raw_value
        log_info_message(
            f"[system_email] Retrieved setting: {key} (sensitive={setting.is_sensitive})"
        )

    return value.strip()


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
    log_info_message(f"[system_email] Preparing email to {to}")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = get_setting("EMAIL_FROM")
    msg["To"] = to

    smtp_host = get_setting("SMTP_HOST")
    smtp_port = int(get_setting("SMTP_PORT"))
    smtp_user = get_setting("SMTP_USER")
    smtp_pass = get_setting("SMTP_PASS", decrypt_value=True)
    use_tls = get_setting("SMTP_USE_TLS") == "1"

    log_info_message(f"[system_email] SMTP host = '{smtp_host}', port = {smtp_port}")
    log_info_message(f"[system_email] Using user: {smtp_user}")

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                log_info_message("[system_email] Starting TLS")
                server.starttls()
            log_info_message("[system_email] Logging in")
            server.login(smtp_user, smtp_pass)
            log_info_message("[system_email] Sending message")
            server.send_message(msg)
        log_info_message("[system_email] Email sent successfully")
    except Exception as e:
        log_exception_with_traceback("[system_email] SMTP error", e)
        raise
