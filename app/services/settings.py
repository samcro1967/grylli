import os
from app.models import db, SystemConfig
from app.services.encryption import encrypt
from sqlalchemy import inspect
from flask import current_app

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

def seed_system_config_from_env():
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
                    key=key,
                    value=value,
                    is_sensitive=is_sensitive,
                    editable=False
                )
                db.session.add(system_entry)
        else:
            config[key] = existing.value  # ← capture existing values too

    db.session.commit()
    return config
