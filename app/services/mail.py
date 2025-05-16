from app.models import SystemConfig
from app.services.encryption import decrypt
from flask import current_app
import smtplib
from email.mime.text import MIMEText
from app.utils.logging import log_info_message, log_error_message


def get_setting(key, decrypt_value=False):
    setting = SystemConfig.query.filter_by(key=key).first()
    if not setting:
        raise ValueError(f"Missing required config setting: {key}")

    raw_value = setting.value
    if decrypt_value and setting.is_sensitive:
        try:
            value = decrypt(raw_value)
        except Exception as e:
            raise ValueError(f"Failed to decrypt {key}: {e}")
    else:
        value = raw_value

    # 🔧 Remove any trailing newlines or spaces
    clean_value = value.strip()

    log_info_message(
        f"get_setting('{key}') -> '{clean_value}' (raw: '{raw_value}', sensitive: {setting.is_sensitive})"
    )
    return clean_value

def send_email(to, subject, body):
    from app.utils.logging import log_info_message

    log_info_message(f"Preparing email to {to}")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = get_setting("EMAIL_FROM")
    msg["To"] = to

    smtp_host = get_setting("SMTP_HOST")
    smtp_port = int(get_setting("SMTP_PORT"))
    smtp_user = get_setting("SMTP_USER")
    smtp_pass = get_setting("SMTP_PASS", decrypt_value=True)
    use_tls   = get_setting("SMTP_USE_TLS") == "1"

    log_info_message(f"SMTP host = '{smtp_host}' (type: {type(smtp_host)}), port = {smtp_port} (type: {type(smtp_port)})")
    log_info_message(f"Using user: {smtp_user}")

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
        log_error_message(f"SMTP error: {e}")
        raise

