from cryptography.fernet import Fernet

from app.core.config import get_settings


def _cipher() -> Fernet:
    return Fernet(get_settings().fernet_key.encode())


def encrypt(plaintext: bytes) -> bytes:
    return _cipher().encrypt(plaintext)


def decrypt(ciphertext: bytes) -> bytes:
    return _cipher().decrypt(ciphertext)
