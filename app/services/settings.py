import os
from app.models import db, SystemConfig
from app.services.encryption import encrypt

DEFAULT_SYSTEM_KEYS = {
    "SMTP_HOST": False,
    "SMTP_PORT": False,
    "SMTP_USER": False,
    "SMTP_PASS": True,
    "EMAIL_FROM": False,
    "EMAIL_DEFAULT_TO": False,
    "FERRET_KEY": True,
    "SMTP_USE_TLS": False,  # ✅ Add this line
}

def seed_system_config_from_env():
    for key, is_sensitive in DEFAULT_SYSTEM_KEYS.items():
        existing = SystemConfig.query.filter_by(key=key).first()
        if not existing:
            value = os.environ.get(key)
            if value is not None:
                if is_sensitive:
                    value = encrypt(value)
                config = SystemConfig(
                    key=key,
                    value=value,
                    is_sensitive=is_sensitive,
                    editable=False  # ✅ we make these view-only
                )
                db.session.add(config)
    db.session.commit()
