"""
# ---------------------------------------------------------------------
# apprise_utils.py
# app/services/apprise_utils.py
# Apprise library test notification utility.
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
from apprise import Apprise


# ---------------------------------------------------------------------
# send_test_apprise_notification
# ---------------------------------------------------------------------
def send_test_apprise_notification(apprise_url):
    """
    Sends a test notification using the Apprise library.

    Args:
        apprise_url: Apprise notification URL.

    Returns:
        Tuple: (success: bool, message: str)
    """
    try:
        print("🔍 Using Apprise library correctly")
        apobj = Apprise()
        apobj.add(apprise_url)

        print(f"🔗 Added Apprise URL: {apprise_url}")

        success = apobj.notify(
            title="Grylli Test", body="✅ This is a test notification from Grylli."
        )

        if success:
            return (True, "Notification sent successfully.")
        else:
            return (False, "Apprise failed to send the notification.")
    except Exception as e:
        return (False, f"Exception: {str(e)}")


# ---------------------------------------------------------------------
# End of file: app/services/apprise_utils.py
# ---------------------------------------------------------------------
