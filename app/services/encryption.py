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

    The string is first encoded to bytes using UTF-8, then encrypted using the Fernet key.
    The result is a URL-safe string.

    Args:
        plaintext: The string to encrypt.

    Returns:
        The encrypted string (base64, URL-safe).

    Raises:
        ValueError: If the FERRET_KEY environment variable is not set or is invalid.
    """
    if not fernet:
        raise ValueError("FERRET_KEY is not set or invalid.")
    return fernet.encrypt(plaintext.encode()).decode()


# ---------------------------------------------------------------------
# decrypt
# ---------------------------------------------------------------------
def decrypt(ciphertext: str) -> str:
    """
    Decrypt an encrypted string using Fernet.

    The encrypted string is first encoded to bytes using UTF-8, then decrypted using the Fernet key.
    The result is a decoded string.

    Args:
        ciphertext: The encrypted string to decrypt.

    Returns:
        The decrypted plaintext string.

    Raises:
        ValueError: If the FERRET_KEY environment variable is not set or is invalid.
    """
    if not fernet:
        raise ValueError("FERRET_KEY is not set or invalid.")
    return fernet.decrypt(ciphertext.encode()).decode()


# ---------------------------------------------------------------------
# End of file: app/services/encryption.py
# ---------------------------------------------------------------------
