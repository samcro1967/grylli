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
from flask_babel import _  # ✅ i18n support

from app.models import SystemConfig
from app.services.encryption import decrypt
from app.utils.logging import log_error_message, log_info_message


# ---------------------------------------------------------------------
# Get Settings
# ---------------------------------------------------------------------
def get_setting(key, decrypt_value=False):
    """
    Fetch a system setting from the database, with optional decryption.

    Args:
        key (str): The config key.
        decrypt_value (bool): Whether to decrypt the value.

    Returns:
        str: The setting value.
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

    clean_value = value.strip()

    log_info_message(
        _("get_setting('%(key)s') -> '%(value)s' (sensitive: %(sensitive)s)")
        % {"key": key, "value": clean_value, "sensitive": setting.is_sensitive}
    )
    return clean_value


# ---------------------------------------------------------------------
# Send mail
# ---------------------------------------------------------------------
def send_email(to, subject, body):
    """
    Send an email using configured SMTP settings.

    Args:
        to (str): Recipient email.
        subject (str): Email subject.
        body (str): Email body.

    Raises:
        Exception: On any SMTP failure.
    """
    log_info_message(_("Preparing email to %(to)s") % {"to": to})

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = get_setting("EMAIL_FROM")
    msg["To"] = to

    smtp_host = get_setting("SMTP_HOST")
    smtp_port = int(get_setting("SMTP_PORT"))
    smtp_user = get_setting("SMTP_USER")
    smtp_pass = get_setting("SMTP_PASS", decrypt_value=True)
    use_tls = get_setting("SMTP_USE_TLS") == "1"

    log_info_message(
        _(
            "SMTP configuration: host=%(host)s (type=%(host_type)s), port=%(port)s (type=%(port_type)s)"
        )
        % {
            "host": smtp_host,
            "host_type": type(smtp_host).__name__,
            "port": smtp_port,
            "port_type": type(smtp_port).__name__,
        }
    )
    log_info_message(_("SMTP username: %(user)s") % {"user": smtp_user})
    log_info_message(_("TLS enabled: %(tls)s") % {"tls": use_tls})

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                log_info_message(_("Starting TLS connection..."))
                server.starttls()
            log_info_message(_("Logging into SMTP server..."))
            server.login(smtp_user, smtp_pass)
            log_info_message(_("Sending email message..."))
            server.send_message(msg)
        log_info_message(_("Email sent successfully to %(to)s") % {"to": to})
    except Exception as e:
        log_error_message(
            _("SMTP error while sending to %(to)s: %(error)s") % {"to": to, "error": str(e)}
        )
        raise
