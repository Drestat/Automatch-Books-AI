"""
Token encryption module for Intuit security compliance.

Uses Fernet (AES-128-CBC + HMAC-SHA256) symmetric encryption.
The FERNET_KEY must be stored separately from the database
(env var or secrets vault), per Intuit requirements.

Generate a key:  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os
from cryptography.fernet import Fernet, InvalidToken

_FERNET_KEY = os.getenv("FERNET_KEY", "")

def _get_fernet() -> Fernet:
    if not _FERNET_KEY:
        raise RuntimeError(
            "FERNET_KEY environment variable is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(_FERNET_KEY.encode())


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token string → base64 ciphertext string."""
    if not plaintext:
        return plaintext
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a base64 ciphertext string → plaintext token."""
    if not ciphertext:
        return ciphertext
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        # Token is likely still in plaintext (pre-migration).
        # Return as-is so the app doesn't crash during migration.
        return ciphertext
