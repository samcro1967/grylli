# ---------------------------------------------------------------------
# email_utils.py
# app/services/smtp/email_utils.py
# SMTP configuration test utility using Apprise CLI for Grylli
# ---------------------------------------------------------------------

import subprocess
import traceback
from urllib.parse import quote

from app.utils.logging import log_error_message, log_info_message


# ---------------------------------------------------------------------
# send_test_smtp
# ---------------------------------------------------------------------
def send_test_smtp(user, smtp_settings):
    """
    Sends a test email using the Apprise CLI with the given SMTP settings.

    Args:
        user: The User object (expects .email for recipient).
        smtp_settings: The user's SMTP config (expects .smtp_username, .smtp_password,
                       .smtp_host, .smtp_port, .use_tls).

    Returns:
        True if Apprise CLI test email was sent successfully, False otherwise.
    """
    try:
        log_info_message(f"📧 Starting SMTP test for user: {user.email}")

        try:
            log_info_message("🔐 Attempting to decode credentials...")
            smtp_username = quote(smtp_settings.smtp_username)
            smtp_password = quote(smtp_settings.smtp_password)  # Decrypted via model
            smtp_host = smtp_settings.smtp_host
            smtp_port = smtp_settings.smtp_port
            secure = "starttls" if smtp_settings.use_tls else "plain"
            recipient = user.email
        except Exception as cred_error:
            log_error_message(f"❌ Failed to prepare credentials: {cred_error}")
            return False

        try:
            log_info_message("🛠 Building Apprise URL...")
            apprise_url = (
                f"mailtos://{smtp_username}:{smtp_password}@{smtp_host}"
                f"?to={recipient}&secure={secure}&port={smtp_port}"
            )
            # log_info_message(f"📨 Apprise URL constructed: {apprise_url}")
        except Exception as url_error:
            log_error_message(f"❌ Failed to build Apprise URL: {url_error}")
            return False

        try:
            log_info_message("🚀 Invoking Apprise CLI...")
            command = [
                "apprise",
                "-vv",
                "-t",
                "Test Notification",
                "-b",
                "This is a test message",
                apprise_url,
            ]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            log_error_message("❌ Apprise CLI not found. Is it installed?")
            return False
        except Exception as subprocess_error:
            log_error_message(f"❌ Error running Apprise CLI: {subprocess_error}")
            return False

        if result.returncode != 0:
            log_error_message(f"❌ Apprise CLI failed with return code {result.returncode}")
            log_error_message(f"📤 STDOUT:\n{result.stdout.strip()}")
            log_error_message(f"📥 STDERR:\n{result.stderr.strip()}")
            return False

        log_info_message("✅ Apprise CLI test email sent successfully.")
        return True

    except Exception as e:
        tb = traceback.format_exc()
        log_error_message(f"❌ Unexpected error in send_test_smtp:\n{e}\n{tb}")
        return False
