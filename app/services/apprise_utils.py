# ---------------------------------------------------------------------
# apprise_utils.py
# app/services/apprise_utils.py
# Apprise library test notification utility.
# ---------------------------------------------------------------------

from apprise import Apprise

from app.utils.logging import log_debug_message, log_exception_with_traceback, log_info_message


def send_test_apprise_notification(apprise_url):
    """
    Sends a test notification using the Apprise library.

    Args:
        apprise_url: Apprise notification URL.

    Returns:
        Tuple: (success: bool, message: str)
    """
    try:
        apobj = Apprise()
        apobj.add(apprise_url)

        success = apobj.notify(
            title="Grylli Test", body="✅ This is a test notification from Grylli."
        )

        if success:
            log_info_message(f"Test Apprise notification succeeded (URL: {apprise_url[:30]}...).")
            return True, "Notification sent successfully."
        else:
            log_info_message(f"Test Apprise notification failed (URL: {apprise_url[:30]}...).")
            return False, "Apprise failed to send the notification."

    except Exception as e:
        log_exception_with_traceback("Exception while sending Apprise notification", e)
        return False, f"Exception: {str(e)}"
