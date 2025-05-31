"""
# ---------------------------------------------------------------------
# webhook.py
# app/services/webhook.py
# System webhook utilities and test notification function.
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
import os

import requests
from flask import current_app
from sqlalchemy import inspect

from app.models import SystemConfig, db
from app.services.encryption import encrypt

# ---------------------------------------------------------------------
# Default system keys for webhook config seeding
# ---------------------------------------------------------------------
DEFAULT_SYSTEM_KEYS = {
    "SMTP_HOST": False,
    "SMTP_PORT": False,
    "SMTP_USER": False,
    "SMTP_PASS": True,
    "EMAIL_FROM": False,
    "EMAIL_DEFAULT_TO": False,
    "FERRET_KEY": True,
    "SMTP_USE_TLS": False,
    "DEBUG": False,
}


# ---------------------------------------------------------------------
# seed_system_config_from_env
# ---------------------------------------------------------------------
def seed_system_config_from_env():
    """
    Seeds system configuration from environment variables.

    - Reads env vars and checks if each is in the DB.
    - If not present, inserts (encrypting if sensitive).
    - Returns a dictionary of seeded (or existing) values.
    """
    config = {}  # ← store values to return

    for key, is_sensitive in DEFAULT_SYSTEM_KEYS.items():
        existing = SystemConfig.query.filter_by(key=key).first()
        if not existing:
            value = os.environ.get(key)
            if value is not None:
                if is_sensitive:
                    value = encrypt(value)
                config[key] = value
                system_entry = SystemConfig(
                    key=key, value=value, is_sensitive=is_sensitive, editable=False
                )
                db.session.add(system_entry)
        else:
            config[key] = existing.value  # ← capture existing values too

    db.session.commit()
    return config


# ---------------------------------------------------------------------
# send_test_webhook_notification
# ---------------------------------------------------------------------
def send_test_webhook_notification(endpoint_url):
    """
    Sends a test JSON payload to the specified webhook endpoint.

    Args:
        endpoint_url: The full webhook URL to send a test notification.

    Returns:
        (success: bool, message: str)
    """
    payload = {"event": "test", "message": "This is a test webhook from Grylli 🧪"}
    try:
        response = requests.post(endpoint_url, json=payload)
        return (response.ok, response.text)
    except Exception as e:
        return (False, str(e))


# ---------------------------------------------------------------------
# End of file: app/services/webhook.py
# ---------------------------------------------------------------------
