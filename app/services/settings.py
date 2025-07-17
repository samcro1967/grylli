"""
# ---------------------------------------------------------------------
# settings.py
# app/services/settings.py
# System settings seeding and retrieval utilities.
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
import os

from flask import current_app, has_request_context
from sqlalchemy import inspect

from app.models import SystemConfig, db
from app.services.encryption import decrypt, encrypt
from app.utils.logging import log_debug_message, log_error_message, log_info_message

# ---------------------------------------------------------------------
# Default system keys and sensitive keys
# ---------------------------------------------------------------------
DEFAULT_SYSTEM_KEYS = {
    "SMTP_HOST": False,
    "SMTP_PORT": False,
    "SMTP_USER": False,
    "SMTP_PASS": True,
    "EMAIL_FROM": False,
    "EMAIL_DEFAULT_TO": False,
    "SMTP_USE_TLS": False,
    "DEBUG": False,
    "SIGNUP_CODE": "YourSuperSecretCode123!",
}
ENCRYPTED_KEYS = {"SMTP_PASS", "SIGNUP_CODE"}


# ---------------------------------------------------------------------
# seed_system_config_from_env
# ---------------------------------------------------------------------
def seed_system_config_from_env():
    """
    Seed the system configuration table from environment variables.

    For each key in DEFAULT_SYSTEM_KEYS:
      - Read the value from the environment.
      - Encrypt if key is sensitive.
      - Insert or update SystemConfig as needed.

    Returns:
        Dictionary of seeded config keys and values.
    """
    config = {}

    for key in DEFAULT_SYSTEM_KEYS:
        try:
            env_value = os.environ.get(key)
            if env_value is None:
                log_info_message(f"[settings] Skipped key '{key}': not found in environment")
                continue

            existing = SystemConfig.query.filter_by(key=key).first()
            is_sensitive = key in ENCRYPTED_KEYS

            # Encrypt if needed
            env_value_encrypted = encrypt(env_value) if is_sensitive else env_value

            if not existing:
                db.session.add(
                    SystemConfig(
                        key=key,
                        value=env_value_encrypted,
                        is_sensitive=is_sensitive,
                        editable=False,
                    )
                )
                log_info_message(
                    f"[settings] Inserted new setting: {key} (sensitive={is_sensitive})"
                )
            else:
                if str(existing.value) != str(env_value_encrypted):
                    log_info_message(
                        f"[settings] Updated setting: {key} (sensitive={is_sensitive})"
                    )
                    existing.value = env_value_encrypted
                    existing.is_sensitive = is_sensitive
                else:
                    log_info_message(f"[settings] Skipped update for '{key}': value unchanged")

            config[key] = env_value_encrypted

        except Exception as e:
            log_error_message(f"[settings] Failed to seed key '{key}': {e}")

    try:
        db.session.commit()
        log_info_message(f"[settings] Seed complete: {list(config.keys())}")
    except Exception as e:
        db.session.rollback()
        log_error_message(f"[settings] Failed to commit seeded config: {e}")
        raise

    return config


# ---------------------------------------------------------------------
# get_setting
# ---------------------------------------------------------------------
def get_setting(key, decrypt_value=False):
    """
    Retrieve a system configuration value from the database.

    Args:
        key: The configuration key to retrieve.
        decrypt_value: If True, decrypt the value if it is sensitive.

    Returns:
        The config value as a string.

    Raises:
        ValueError: If the key does not exist or decryption fails.
    """


def get_setting(key, decrypt_value=False):
    """
    Retrieve a system configuration value from the database.

    Args:
        key: The configuration key to retrieve.
        decrypt_value: If True, decrypt the value if it is sensitive.

    Returns:
        The config value as a string.

    Raises:
        ValueError: If the key does not exist or decryption fails.
    """
    try:
        setting = SystemConfig.query.filter_by(key=key).first()
    except Exception as e:
        log_error_message(f"[settings] DB error while retrieving key '{key}': {e}")
        raise ValueError(f"Database error retrieving setting '{key}'")

    if not setting:
        log_error_message(f"[settings] Missing required config key: {key}")
        raise ValueError(f"Missing required config setting: {key}")

    value = setting.value

    if decrypt_value and setting.is_sensitive:
        try:
            value = decrypt(value)
            log_info_message(f"[settings] Decrypted setting: {key}")
        except Exception as e:
            log_error_message(f"[settings] Decryption failed for {key}: {e}")
            raise ValueError(f"Failed to decrypt {key}: {e}")
    else:
        log_debug_message(f"[settings] Retrieved setting: {key} (sensitive={setting.is_sensitive})")

    return value.strip()
