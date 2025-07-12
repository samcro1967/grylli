"""
auth_helpers.py
app/services/auth_helpers.py

Helper functions for token generation and verification used in auth flows.
"""

from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def generate_token(email: str, salt: str) -> str:
    """
    Generate a secure token for the given email and salt.
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt=salt)


def verify_token(token: str, salt: str, expiration: int = None) -> str | None:
    """
    Verify a secure token and return the email if valid, or None.
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return s.loads(
            token,
            salt=salt,
            max_age=expiration or current_app.config["TOKEN_EXPIRATION_SECONDS"],
        )
    except Exception:
        return None
