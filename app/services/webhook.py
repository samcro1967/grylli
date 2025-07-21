"""
# ---------------------------------------------------------------------
# webhook.py
# app/services/webhook.py
# System webhook utilities and test notification function.
# ---------------------------------------------------------------------
"""

import os

import requests
from flask import current_app
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

from app.models import SystemConfig, db
from app.services.encryption import encrypt
from app.utils.logging import log_error_message, log_exception_with_traceback, log_info_message

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
# Internal: Get username safely
# ---------------------------------------------------------------------
def _get_username():
    try:
        return current_user.username
    except Exception:
        return "unknown"


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

    try:
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
                        SystemConfig(
                            key=key, value=value, is_sensitive=is_sensitive, editable=False
                        )
                    )
            else:
                log_info_message(f"[webhook] Found existing config: {key}")
                config[key] = existing.value

        db.session.commit()
        log_info_message("[webhook] System config seeding complete.")

    except SQLAlchemyError as e:
        db.session.rollback()
        log_exception_with_traceback("[webhook] DB error during config seeding", e)
        raise

    except Exception as e:
        log_exception_with_traceback("[webhook] General error during config seeding", e)
        raise

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
    user = _get_username()
    payload = {"event": "test", "message": "This is a test webhook from Grylli 🧪"}

    log_info_message(f"[webhook] Sending test notification to: {endpoint_url} (user: {user})")

    try:
        response = requests.post(endpoint_url, json=payload, timeout=5)
        if response.ok:
            log_info_message(
                f"[webhook] Webhook test success (user: {user}, status={response.status_code})"
            )
        else:
            log_error_message(
                f"[webhook] Webhook test failed (user: {user}, status={response.status_code}, response={response.text})"
            )
        return (response.ok, response.text)
    except Exception as e:
        log_exception_with_traceback(f"[webhook] Exception during webhook test (user: {user})", e)
        return (False, str(e))
