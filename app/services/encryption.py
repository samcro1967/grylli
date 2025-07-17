"""
# ---------------------------------------------------------------------
# encryption.py
# app/services/encryption.py
# Symmetric string encryption/decryption with Fernet.
# ---------------------------------------------------------------------
"""

import os

from cryptography.fernet import Fernet
from flask_login import current_user

from app.utils.logging import log_debug_message, log_exception_with_traceback, log_info_message

__all__ = ["encrypt", "decrypt"]

FERRET_KEY = os.environ.get("FERRET_KEY")
fernet = Fernet(FERRET_KEY.encode()) if FERRET_KEY else None


def _get_username():
    try:
        return current_user.username
    except Exception:
        return "unknown"


def encrypt(plaintext: str) -> str:
    """
    Encrypt a plaintext string using Fernet.

    Args:
        plaintext: The string to encrypt.

    Returns:
        The encrypted string (base64, URL-safe).

    Raises:
        ValueError: If the FERRET_KEY environment variable is not set or is invalid.
    """
    if not fernet:
        log_info_message("Encryption failed: FERRET_KEY is not set or invalid.")
        raise ValueError("FERRET_KEY is not set or invalid.")
    try:
        encrypted = fernet.encrypt(plaintext.encode()).decode()
        log_debug_message(f"[ENCRYPT] String encrypted successfully by '{_get_username()}'.")
        return encrypted
    except Exception as e:
        log_info_message(f"[ENCRYPT] Exception raised by '{_get_username()}'.")
        log_exception_with_traceback("Encryption error", e)
        raise


def decrypt(ciphertext: str) -> str:
    """
    Decrypt an encrypted string using Fernet.

    Args:
        ciphertext: The encrypted string to decrypt.

    Returns:
        The decrypted plaintext string.

    Raises:
        ValueError: If the FERRET_KEY environment variable is not set or is invalid.
    """
    if not fernet:
        log_info_message("Decryption failed: FERRET_KEY is not set or invalid.")
        raise ValueError("FERRET_KEY is not set or invalid.")
    try:
        decrypted = fernet.decrypt(ciphertext.encode()).decode()
        log_debug_message(f"[DECRYPT] String decrypted successfully by '{_get_username()}'.")
        return decrypted
    except Exception as e:
        log_info_message(f"[DECRYPT] Exception raised by '{_get_username()}'.")
        log_exception_with_traceback("Decryption error", e)
        raise
