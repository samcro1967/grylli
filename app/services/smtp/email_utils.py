"""
# ---------------------------------------------------------------------
# email_utils.py
# app/services/smtp/email_utils.py
# SMTP configuration test utility using Apprise CLI for Grylli
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
import subprocess
from urllib.parse import quote

from app.services.encryption import decrypt
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
                       .smtp_host).

    Returns:
        True if Apprise CLI test email was sent successfully, False otherwise.

    Logging:
        - log_info_message for each high-level step.
        - log_error_message for any failures or command output.
    """
    try:
        log_info_message("🔐 Attempting to decrypt SMTP password...")

        # Prepare the SMTP username (URL-encoded) and extract connection details
        smtp_username = quote(smtp_settings.smtp_username)
        smtp_password = smtp_settings.smtp_password  # Already decrypted if passed in
        smtp_host = smtp_settings.smtp_host
        recipient = user.email

        log_info_message("🛠 Building Apprise command...")

        # Construct the Apprise URL in mailtos:// format (with STARTTLS by default)
        apprise_url = (
            f"mailtos://{smtp_username}:{smtp_password}@{smtp_host}"
            f"?to={recipient}&secure=starttls"
        )

        # Assemble the CLI command
        command = [
            "apprise",
            "-vv",
            "-t",
            "Test Notification",
            "-b",
            "This is a test message",
            apprise_url,
        ]

        # Run the Apprise CLI command and capture output
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            log_error_message(f"❌ Apprise CLI failed with return code {result.returncode}")
            log_error_message(f"STDOUT:\n{result.stdout}")
            log_error_message(f"STDERR:\n{result.stderr}")
            return False

        log_info_message("✅ Apprise CLI test email sent successfully.")
        return True

    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        log_error_message(f"❌ Error in send_test_smtp:\n{e}\n{tb}")
        return False
