"""
# ---------------------------------------------------------------------
# apprise_utils.py
# app/services/scheduler/apprise_utils.py
# Execute Apprise notification for expired messages
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
from apprise import Apprise

from app.models import AppriseURL
from app.utils.logging import log_error_message, log_info_message


# ---------------------------------------------------------------------
# execute_apprise
# ---------------------------------------------------------------------
def execute_apprise(message):
    """
    Send an Apprise notification for the given message using all linked Apprise URLs.

    Args:
        message: The message object with .label, .subject, .content, and .apprise_destinations.

    Logging:
        - log_info_message for high-level events.
        - log_error_message for failures or exceptions.
    """
    log_info_message(f"🔔 Executing Apprise for message: {message.label}")

    try:
        if not message.apprise_destinations:
            log_info_message("⚠️ No Apprise destinations linked to this message.")
            return

        apobj = Apprise()
        for destination in message.apprise_destinations:
            if destination.enabled:
                try:
                    apobj.add(destination.url)
                except Exception as e:
                    log_error_message(f"❌ Failed to add Apprise URL [{destination.label}]: {e}")

        title = f"[Grylli] {message.subject}"
        body = message.content

        if not apobj.notify(title=title, body=body):
            log_error_message(f"❌ Failed to send Apprise notification for: {message.label}")
        else:
            log_info_message(f"✅ Apprise notification sent for: {message.label}")

    except Exception as e:
        log_error_message(f"❌ Unexpected error while executing Apprise: {e}")
