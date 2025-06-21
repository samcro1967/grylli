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
from app.utils.logging import log_error_message, log_info_message

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
    config = {}

    for key, is_sensitive in DEFAULT_SYSTEM_KEYS.items():
        existing = SystemConfig.query.filter_by(key=key).first()
        if not existing:
            value = os.environ.get(key)
            if value is not None:
                log_info_message(f"[webhook] Seeding key: {key} (sensitive={is_sensitive})")
                if is_sensitive:
                    value = encrypt(value)
                config[key] = value
                db.session.add(
                    SystemConfig(key=key, value=value, is_sensitive=is_sensitive, editable=False)
                )
        else:
            log_info_message(f"[webhook] Found existing config: {key}")
            config[key] = existing.value

    db.session.commit()
    log_info_message("[webhook] System config seeding complete.")
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

    log_info_message(f"[webhook] Sending test notification to: {endpoint_url}")
    try:
        response = requests.post(endpoint_url, json=payload)
        if response.ok:
            log_info_message(f"[webhook] Webhook test success (status={response.status_code})")
        else:
            log_error_message(
                f"[webhook] Webhook test failed (status={response.status_code}, response={response.text})"
            )
        return (response.ok, response.text)
    except Exception as e:
        log_error_message(f"[webhook] Exception during webhook test: {e}")
        return (False, str(e))
