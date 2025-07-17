# ---------------------------------------------------------------------
# apprise_utils.py
# app/services/scheduler/apprise_utils.py
# Execute Apprise notification for expired messages
# ---------------------------------------------------------------------

import traceback

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
    try:
        log_info_message(
            f"Scheduler [ExecuteApprise] - Success - Executing Apprise for message: {getattr(message, 'label', '[unknown label]')}"
        )

        if not getattr(message, "apprise_destinations", None):
            log_info_message(
                "Scheduler [ExecuteApprise] - Success - No Apprise destinations linked to this message."
            )
            return

        apobj = Apprise()

        for destination in message.apprise_destinations:
            if destination.enabled:
                try:
                    apobj.add(destination.url)
                    log_info_message(
                        f"Scheduler [ExecuteApprise] - Success - Added Apprise URL: {destination.label} ({destination.url})"
                    )
                except Exception as e:
                    log_error_message(
                        f"ERROR - Scheduler [ExecuteApprise] - Failure - Failed to add Apprise URL [{destination.label}]: {e}"
                    )

        try:
            title = f"[Grylli] {message.subject}"
            body = message.content
        except Exception as e:
            log_error_message(
                f"ERROR - Scheduler [ExecuteApprise] - Failure - Failed to extract message content: {e}"
            )
            return

        try:
            if not apobj.notify(title=title, body=body):
                log_error_message(
                    f"ERROR - Scheduler [ExecuteApprise] - Failure - Failed to send Apprise notification for: {message.label}"
                )
            else:
                log_info_message(
                    f"Scheduler [ExecuteApprise] - Success - Apprise notification sent for: {message.label}"
                )
        except Exception as notify_error:
            tb = traceback.format_exc()
            log_error_message(
                f"ERROR - Scheduler [ExecuteApprise] - Failure - Exception during Apprise notify(): {notify_error}\n{tb}"
            )

    except Exception as e:
        tb = traceback.format_exc()
        log_error_message(
            f"ERROR - Scheduler [ExecuteApprise] - Failure - Unexpected error in execute_apprise:\n{e}\n{tb}"
        )
