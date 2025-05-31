from app.models import SystemConfig
from app.services.encryption import decrypt
from flask import current_app
import smtplib
from email.mime.text import MIMEText
from app.utils.logging import log_info_message, log_error_message
from flask_babel import _  # ✅ i18n support

def get_setting(key, decrypt_value=False):
    setting = SystemConfig.query.filter_by(key=key).first()
    if not setting:
        raise ValueError(_("Missing required config setting: ") + key)

    raw_value = setting.value
    if decrypt_value and setting.is_sensitive:
        try:
            value = decrypt(raw_value)
        except Exception as e:
            raise ValueError(_("Failed to decrypt %(key)s: %(error)s") % {
                "key": key,
                "error": str(e)
            })
    else:
        value = raw_value

    # 🔧 Remove any trailing newlines or spaces
    clean_value = value.strip()

    log_info_message(_("get_setting('%(key)s') -> '%(value)s' (raw: '%(raw)s', sensitive: %(sensitive)s)") % {
        "key": key,
        "value": clean_value,
        "raw": raw_value,
        "sensitive": setting.is_sensitive
    })
    return clean_value

def send_email(to, subject, body):
    from app.utils.logging import log_info_message

    log_info_message(_("Preparing email to %(to)s") % {"to": to})

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = get_setting("EMAIL_FROM")
    msg["To"] = to

    smtp_host = get_setting("SMTP_HOST")
    smtp_port = int(get_setting("SMTP_PORT"))
    smtp_user = get_setting("SMTP_USER")
    smtp_pass = get_setting("SMTP_PASS", decrypt_value=True)
    use_tls   = get_setting("SMTP_USE_TLS") == "1"

    log_info_message(_("SMTP host = '%(host)s' (type: %(host_type)s), port = %(port)s (type: %(port_type)s)") % {
        "host": smtp_host,
        "host_type": type(smtp_host),
        "port": smtp_port,
        "port_type": type(smtp_port)
    })
    log_info_message(_("Using user: %(user)s") % {"user": smtp_user})

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                log_info_message(_("Starting TLS"))
                server.starttls()
            log_info_message(_("Logging in"))
            server.login(smtp_user, smtp_pass)
            log_info_message(_("Sending message"))
            server.send_message(msg)
        log_info_message(_("Email sent successfully"))
    except Exception as e:
        log_error_message(_("SMTP error: ") + str(e))
        raise
