# ---------------------------------------------------------------------
# email_utils.py
# app/services/scheduler/email_utils.py
# Email-related actions for check-ins and secure delivery
# ---------------------------------------------------------------------

import os
import smtplib
import traceback
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode

from app.extensions import db
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
    try:
        if html_body:
            msg = MIMEMultipart("alternative")
        else:
            msg = MIMEMultipart()

        msg["From"] = smtp_settings.smtp_username
        msg["To"] = recipient_email
        msg["Subject"] = subject

        log_debug_message("Scheduler [SendEmail] - Success - Attaching plain text body")
        msg.attach(MIMEText(text_body, "plain"))
        if html_body:
            log_debug_message("Scheduler [SendEmail] - Success - Attaching HTML body")
            msg.attach(MIMEText(html_body, "html"))

        if attachments:
            log_debug_message(
                f"Scheduler [SendEmail] - Success - Attaching {len(attachments)} file(s)"
            )
            for file_path in attachments:
                part = MIMEBase("application", "octet-stream")
                with open(file_path, "rb") as f:
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", f"attachment; filename={os.path.basename(file_path)}"
                )
                msg.attach(part)

        password = smtp_settings.smtp_password

        log_debug_message(
            f"Scheduler [SendEmail] - Success - SMTP Host: {smtp_settings.smtp_host}, Port: {smtp_settings.smtp_port}, "
            f"User: {smtp_settings.smtp_username}, TLS: {smtp_settings.use_tls}"
        )

        smtp_class = smtplib.SMTP_SSL if not smtp_settings.use_tls else smtplib.SMTP
        smtp = smtp_class(smtp_settings.smtp_host, smtp_settings.smtp_port)
        smtp.ehlo()

        if smtp_settings.use_tls:
            smtp.starttls()

        smtp.login(smtp_settings.smtp_username, password)
        smtp.send_message(msg)
        smtp.quit()

        log_info_message(f"Scheduler [SendEmail] - Success - Email sent to {recipient_email}")
        return True

    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [SendEmail] - Failure - Failed to send email to {recipient_email}: {e}"
        )
        log_error_message(traceback.format_exc())
        return False


# ---------------------------------------------------------------------
# send_checkin_email
# ---------------------------------------------------------------------
def send_checkin_email(user, item):
    """
    Send a check-in reminder email to the user for a pending item (message or secure email).
    """
    try:
        log_info_message(
            f"Scheduler [SendCheckinEmail] - Success - User '{user.username}' — Sending check-in reminder to {user.email} for {item.label}"
        )

        smtp_settings = UserMailSettings.query.filter_by(user_id=user.id).first()
        log_debug_message(
            f"Scheduler [SendCheckinEmail] - Success - SMTP settings fetched: {smtp_settings}, enabled: {getattr(smtp_settings, 'enabled', None)}"
        )

        if not smtp_settings or not smtp_settings.enabled:
            log_error_message(
                f"ERROR - Scheduler [SendCheckinEmail] - Failure - SMTP settings not found or disabled for user {user.id}"
            )
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

        success = _send_email(user.email, subject, text_body, smtp_settings, html_body=html_body)
        if not success:
            log_error_message(
                f"ERROR - Scheduler [SendCheckinEmail] - Failure - Reminder email failed for {item.label}"
            )

    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [SendCheckinEmail] - Failure - Exception in send_checkin_email: {e}"
        )
        log_error_message(traceback.format_exc())


# ---------------------------------------------------------------------
# send_secure_email
# ---------------------------------------------------------------------
def send_secure_email(item):
    """
    Send a secure message with attachments to the intended recipient using the owner's SMTP settings.
    """
    try:
        user = db.session.get(User, item.user_id)
        smtp_settings = UserMailSettings.query.filter_by(user_id=user.id).first() if user else None

        log_info_message(
            f"Scheduler [SendSecureEmail] - Success - User '{user.username}' — Sending email: {item.label} → {item.recipient}"
        )

        if not smtp_settings or not smtp_settings.enabled:
            log_error_message(
                f"ERROR - Scheduler [SendSecureEmail] - Failure - SMTP settings not found or disabled for user {user.id}"
            )
            return

        subject = item.subject
        body = item.body
        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads"))
        attachments = [os.path.join(upload_dir, f.file_path) for f in item.files if f.file_path]

        _send_email(item.recipient, subject, body, smtp_settings, attachments=attachments)

    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [SendSecureEmail] - Failure - Exception in send_secure_email for {getattr(item, 'label', 'unknown')}: {e}"
        )
        log_error_message(traceback.format_exc())


# ---------------------------------------------------------------------
# send_owner_notice
# ---------------------------------------------------------------------
def send_owner_notice(item):
    """
    Notify the owner via email that their scheduled item was executed due to missed check-in.
    """
    try:
        user = db.session.get(User, item.user_id)
        smtp_settings = UserMailSettings.query.filter_by(user_id=user.id).first() if user else None

        if not user:
            log_error_message(
                f"ERROR - Scheduler [SendOwnerNotice] - Failure - User not found for item {item.label} (user_id={item.user_id})"
            )
            return

        if not smtp_settings or not smtp_settings.enabled:
            log_error_message(
                f"ERROR - Scheduler [SendOwnerNotice] - Failure - SMTP settings not found or disabled for user {user.id}"
            )
            return

        subject = f"[Grylli] Final Notice: {item.label} was executed"

        delivery_line = (
            f"was delivered to {item.recipient} " if hasattr(item, "recipient") else "was executed "
        )

        body = (
            f"Hello {user.username},\n\n"
            f'Your scheduled item titled "{item.label}" {delivery_line}'
            f"because you did not check in during the specified interval and grace period.\n\n"
            f"This action was performed automatically as scheduled.\n\n"
            f"- Grylli"
        )

        log_info_message(
            f"Scheduler [SendOwnerNotice] - Success - User '{user.username}' — Sent final notice for {item.label} to {user.email}"
        )
        _send_email(user.email, subject, body, smtp_settings)

    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [SendOwnerNotice] - Failure - Exception in send_owner_notice: {e}"
        )
        log_error_message(traceback.format_exc())


# ---------------------------------------------------------------------
# send_reminder_email
# ---------------------------------------------------------------------
def send_reminder_email(reminder):
    """
    Sends the reminder content to the owner (reminder.user.email) via SMTP.
    Used for generic reminders (not EmailMessages).
    """
    try:
        user = db.session.get(User, reminder.user_id)
        smtp = UserMailSettings.query.filter_by(user_id=reminder.user_id, enabled=True).first()

        if not user:
            log_error_message(
                f"ERROR - Scheduler [SendReminderEmail] - Failure - Reminder email failed — user not found for reminder {reminder.label}"
            )
            return

        if not smtp:
            log_error_message(
                f"ERROR - Scheduler [SendReminderEmail] - Failure - Reminder email failed — no SMTP config for user {reminder.user_id}"
            )
            return

        subject = f"[Grylli] {reminder.subject}"
        body = reminder.content or f"You have a reminder: {reminder.label}"

        log_info_message(
            f"Scheduler [SendReminderEmail] - Success - User '{user.username}' — Sending reminder email to {user.email} via SMTP config {smtp.id}"
        )
        success = _send_email(user.email, subject, body, smtp)

        if not success:
            log_error_message(
                f"ERROR - Scheduler [SendReminderEmail] - Failure - Reminder email failed to send for {reminder.label}"
            )

    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [SendReminderEmail] - Failure - Exception in send_reminder_email: {e}"
        )
        log_error_message(traceback.format_exc())
