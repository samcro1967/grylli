"""
# ---------------------------------------------------------------------
# encryption.py
# app/services/encryption.py
# Symmetric string encryption/decryption with Fernet.
# ---------------------------------------------------------------------
"""

import os

# ------------------------ Imports (PEP8 order) -----------------------
from cryptography.fernet import Fernet

from app.utils.logging import log_exception_with_traceback, log_info_message

# ---------------------------------------------------------------------
# Fernet key and utility setup
# ---------------------------------------------------------------------
__all__ = ["encrypt", "decrypt"]

FERRET_KEY = os.environ.get("FERRET_KEY")
fernet = Fernet(FERRET_KEY.encode()) if FERRET_KEY else None


# ---------------------------------------------------------------------
# encrypt
# ---------------------------------------------------------------------
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
        log_info_message("String encrypted successfully.")
        return encrypted
    except Exception as e:
        log_exception_with_traceback("Encryption error", e)
        raise


# ---------------------------------------------------------------------
# decrypt
# ---------------------------------------------------------------------
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
        log_info_message("String decrypted successfully.")
        return decrypted
    except Exception as e:
        log_exception_with_traceback("Decryption error", e)
        raise
