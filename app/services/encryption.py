from cryptography.fernet import Fernet
import os


__all__ = ["encrypt", "decrypt"]

FERRET_KEY = os.environ.get("FERRET_KEY")
fernet = Fernet(FERRET_KEY.encode()) if FERRET_KEY else None

def encrypt(plaintext: str) -> str:
    if not fernet:
        raise ValueError("FERRET_KEY is not set or invalid.")
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt(ciphertext: str) -> str:
    if not fernet:
        raise ValueError("FERRET_KEY is not set or invalid.")
    return fernet.decrypt(ciphertext.encode()).decode()
