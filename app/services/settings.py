"""
# ---------------------------------------------------------------------
# settings.py
# app/services/settings.py
# System settings seeding and retrieval utilities.
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
import os

from flask import current_app
from sqlalchemy import inspect

from app.models import SystemConfig, db
from app.services.encryption import decrypt, encrypt

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
    "FERRET_KEY": True,
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
        env_value = os.environ.get(key)
        if env_value is None:
            continue

        existing = SystemConfig.query.filter_by(key=key).first()
        is_sensitive = key in ENCRYPTED_KEYS

        # Always encrypt if sensitive
        if is_sensitive:
            env_value_encrypted = encrypt(env_value)
        else:
            env_value_encrypted = env_value

        if not existing:
            db.session.add(
                SystemConfig(
                    key=key, value=env_value_encrypted, is_sensitive=is_sensitive, editable=False
                )
            )
        else:
            # Only update if stored value differs
            if str(existing.value) != str(env_value_encrypted):
                existing.value = env_value_encrypted
                existing.is_sensitive = is_sensitive

        config[key] = env_value_encrypted

    db.session.commit()
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
    setting = SystemConfig.query.filter_by(key=key).first()
    if not setting:
        raise ValueError(f"Missing required config setting: {key}")

    value = setting.value
    if decrypt_value and setting.is_sensitive:
        try:
            value = decrypt(value)
        except Exception as e:
            raise ValueError(f"Failed to decrypt {key}: {e}")

    return value.strip()


# ---------------------------------------------------------------------
# End of file: app/services/settings.py
# ---------------------------------------------------------------------
