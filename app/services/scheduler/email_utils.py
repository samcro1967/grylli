"""
# ---------------------------------------------------------------------
# email_utils.py
# app/services/scheduler/email_utils.py
# Email-related actions for check-ins and secure delivery
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode

from app.models import EmailMessage, User, UserMailSettings
from app.utils.logging import log_debug_message, log_error_message, log_info_message


# ---------------------------------------------------------------------
# _send_email (internal helper)
# ---------------------------------------------------------------------
def _send_email(
    recipient_email, subject, text_body, smtp_settings, html_body=None, attachments=None
):
    """
    Send an email with optional HTML content and attachments using provided SMTP settings.
    """
    import traceback

    try:
        # Decide the MIME structure based on HTML presence
        if html_body:
            msg = MIMEMultipart("alternative")
        else:
            msg = MIMEMultipart()

        msg["From"] = smtp_settings.smtp_username
        msg["To"] = recipient_email
        msg["Subject"] = subject

        log_debug_message("Attaching plain text body")
        msg.attach(MIMEText(text_body, "plain"))
        if html_body:
            log_debug_message("Attaching HTML body")
            msg.attach(MIMEText(html_body, "html"))

        if attachments:
            log_debug_message(f"Attaching {len(attachments)} file(s)")
            for file_path in attachments:
                part = MIMEBase("application", "octet-stream")
                with open(file_path, "rb") as f:
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", f"attachment; filename={os.path.basename(file_path)}"
                )
                msg.attach(part)

        # Access decrypted password via model property (already decrypted)
        password = smtp_settings.smtp_password
        fernet_key = os.environ.get("FERNET_KEY", "NO_KEY_SET")

        log_debug_message(f"Using Fernet key (truncated): {fernet_key[:8]}...")
        log_debug_message(
            f"SMTP Host: {smtp_settings.smtp_host}, Port: {smtp_settings.smtp_port}, User: {smtp_settings.smtp_username}, Use TLS: {smtp_settings.use_tls}"
        )
        log_debug_message(f"Decrypted SMTP password length: {len(password) if password else 0}")

        smtp_class = smtplib.SMTP_SSL if not smtp_settings.use_tls else smtplib.SMTP
        smtp = smtp_class(smtp_settings.smtp_host, smtp_settings.smtp_port)
        smtp.ehlo()

        if smtp_settings.use_tls:
            smtp.starttls()

        smtp.login(smtp_settings.smtp_username, password)
        smtp.send_message(msg)
        smtp.quit()

        log_info_message(f"✅ Email sent to {recipient_email}")
        return True

    except Exception as e:
        log_error_message(f"❌ Failed to send email to {recipient_email}: {e}")
        log_error_message(traceback.format_exc())
        return False


# ---------------------------------------------------------------------
# send_checkin_email
# ---------------------------------------------------------------------
def send_checkin_email(user, item):
    """
    Send a check-in reminder email to the user for a pending item (message or secure email).

    Args:
        user: User object to notify.
        item: Message or EmailMessage object.

    Logging:
        - log_info_message for major events.
        - log_error_message for failures.
    """
    log_info_message(f"✉️ Sending check-in reminder to {user.email} for {item.label}")

    smtp_settings = UserMailSettings.query.filter_by(user_id=user.id).first()
    log_debug_message(
        f"SMTP settings fetched: {smtp_settings}, enabled: {getattr(smtp_settings, 'enabled', None)}"
    )
    if not smtp_settings or not smtp_settings.enabled:
        log_error_message(f"⚠️ SMTP settings not found or disabled for user {user.id}")
        return

    subject = f"[Grylli] Check-in Reminder: {item.label}"

    fqdn = os.environ.get("FQDN", "http://localhost:5000").rstrip("/")
    base_url = os.environ.get("BASE_URL", "").strip("/")
    checkin_type = "email" if isinstance(item, EmailMessage) else "message"

    params = urlencode({"type": checkin_type, "id": item.id, "user": user.id})
    checkin_url = f"{fqdn}/{base_url}/checkin?{params}"

    text_body = (
        f"Hello {user.username},\n\n"
        f"This is a friendly reminder to check in for your message: {item.label}.\n\n"
        f"Click the link below to check in now:\n{checkin_url}\n\n"
        f"- Grylli"
    )
    html_body = f"""
    <html>
      <body>
        <p>Hello {user.username},</p>
        <p>This is a friendly reminder to check in for your message: <strong>{item.label}</strong>.</p>
        <p><a href="{checkin_url}">✅ Click here to check in</a></p>
        <p>- Grylli</p>
      </body>
    </html>
    """

    log_debug_message(
        f"Calling _send_email with to={user.email}, subject='{subject}', "
        f"smtp_settings.id={smtp_settings.id if smtp_settings else None}, smtp_enabled={smtp_settings.enabled if smtp_settings else None}"
    )

    success = _send_email(user.email, subject, text_body, smtp_settings, html_body=html_body)
    if not success:
        log_error_message(f"❌ Reminder email failed for {item.label}")


# ---------------------------------------------------------------------
# send_secure_email
# ---------------------------------------------------------------------
def send_secure_email(item):
    """
    Send a secure message with attachments to the intended recipient using the owner's SMTP settings.

    Args:
        item: EmailMessage instance (must have .user_id, .recipient, .subject, .body, .files).

    Logging:
        - log_info_message for send attempt.
        - log_error_message for missing SMTP config.
    """
    user = User.query.get(item.user_id)
    smtp_settings = UserMailSettings.query.filter_by(user_id=user.id).first() if user else None

    log_info_message(f"📤 Sending email: {item.label} → {item.recipient}")

    if not smtp_settings or not smtp_settings.enabled:
        log_error_message(f"⚠️ SMTP settings not found or disabled for user {user.id}")
        return

    subject = item.subject
    body = item.body
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads"))
    attachments = [os.path.join(upload_dir, f.file_path) for f in item.files if f.file_path]

    _send_email(item.recipient, subject, body, smtp_settings, attachments=attachments)


# ---------------------------------------------------------------------
# send_owner_notice
# ---------------------------------------------------------------------
def send_owner_notice(item):
    """
    Notify the owner via email that their scheduled item was executed due to missed check-in.

    Args:
        item: Message or EmailMessage object with .label, .user_id, etc.

    Logging:
        - log_error_message if user not found or SMTP missing.
    """
    user = User.query.get(item.user_id)
    smtp_settings = UserMailSettings.query.filter_by(user_id=user.id).first() if user else None
    if not user:
        log_error_message(f"❌ User not found for item {item.label} (user_id={item.user_id})")
        return

    if not smtp_settings or not smtp_settings.enabled:
        log_error_message(f"⚠️ Cannot notify user {user.id} — SMTP not configured or disabled")
        return

    subject = f"[Grylli] Final Notice: {item.label} was executed"

    if hasattr(item, "recipient"):
        delivery_line = f"was delivered to {item.recipient} "
    else:
        delivery_line = "was executed "

    body = (
        f"Hello {user.username},\n\n"
        f'Your scheduled item titled "{item.label}" {delivery_line}'
        f"because you did not check in during the specified interval and grace period.\n\n"
        f"This action was performed automatically as scheduled.\n\n"
        f"- Grylli"
    )

    _send_email(user.email, subject, body, smtp_settings)
