"""
# ---------------------------------------------------------------------
# serialization.py
# utils/serialization.py
# System settings seeding and retrieval utilities.
# ---------------------------------------------------------------------
"""

import json

from app.services.encryption import decrypt


def model_to_dict(obj, decrypted_fields=None, exclude_fields=None):
    """
    Serialize a SQLAlchemy model to dict.
    - decrypted_fields: list of property names to use instead of DB columns (for decryption)
    - exclude_fields: list of fields to skip (e.g., password_hash)
    """
    if decrypted_fields is None:
        decrypted_fields = []
    if exclude_fields is None:
        exclude_fields = []

    result = {}
    for column in obj.__table__.columns:
        key = column.name
        if key in exclude_fields:
            continue
        result[key] = getattr(obj, key)

    for key in decrypted_fields:
        if key == "mfa_recovery_codes":
            # Decrypt and parse codes as list
            encrypted = getattr(obj, "mfa_recovery_codes", None)
            if encrypted:
                try:
                    decrypted = decrypt(encrypted)
                    try:
                        codes = json.loads(decrypted)
                        if not isinstance(codes, list):
                            codes = [decrypted]
                    except Exception:
                        codes = [c.strip() for c in decrypted.split(",") if c.strip()]
                    result[key] = codes
                except Exception as exc:
                    result[key] = [f"ERROR_DECRYPTING: {exc}"]
            else:
                result[key] = []
        elif hasattr(obj, key):
            result[key] = getattr(obj, key)

    for key, value in result.items():
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    return result
