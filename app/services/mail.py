"""
# ---------------------------------------------------------------------
# mail.py
# app/services/mail.py
# Mail send utility
# ---------------------------------------------------------------------
"""

import smtplib
from email.mime.text import MIMEText

from flask import current_app
from flask_babel import _
from flask_login import current_user

from app.models import SystemConfig
from app.services.encryption import decrypt
from app.utils.logging import log_error_message, log_info_message


def _get_username():
    try:
        return current_user.username
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------
# Get Settings
# ---------------------------------------------------------------------
def get_setting(key, decrypt_value=False):
    """
    Fetch a system setting from the database, with optional decryption.
    """
    setting = SystemConfig.query.filter_by(key=key).first()
    if not setting:
        log_error_message(f"Missing required config setting: {key}")
        raise ValueError(_("Missing required config setting: ") + key)

    raw_value = setting.value
    if decrypt_value and setting.is_sensitive:
        try:
            value = decrypt(raw_value)
        except Exception as e:
            log_error_message(f"Decryption failed for key={key}: {e}")
            raise ValueError(
                _("Failed to decrypt %(key)s: %(error)s") % {"key": key, "error": str(e)}
            )
    else:
        value = raw_value

    return value.strip()


# ---------------------------------------------------------------------
# Send mail
# ---------------------------------------------------------------------
def send_email(to, subject, body):
    """
    Send an email using configured SMTP settings.
    """
    log_info_message(f"Preparing email to '{to}' (by '{_get_username()}')")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = get_setting("EMAIL_FROM")
    msg["To"] = to

    smtp_host = get_setting("SMTP_HOST")
    smtp_port = int(get_setting("SMTP_PORT"))
    smtp_user = get_setting("SMTP_USER")
    smtp_pass = get_setting("SMTP_PASS", decrypt_value=True)
    use_tls = get_setting("SMTP_USE_TLS") == "1"

    # Don't log SMTP credentials, TLS logs are fine
    log_info_message(f"SMTP connection: host={smtp_host}, port={smtp_port}, TLS={use_tls}")

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        log_info_message(f"Email sent to '{to}' by '{_get_username()}'")
    except Exception as e:
        log_error_message(f"SMTP error while sending to '{to}' by '{_get_username()}': {str(e)}")
        raise
