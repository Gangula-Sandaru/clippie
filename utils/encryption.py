"""
Fernet-based content encryption for Clippie.

A 256-bit key is generated on first run and stored at:
    AppData\\Roaming\\Clippie\\clippie.key  (Windows)
    ~/.clippie/clippie.key                 (other platforms)

Security note:
    The key lives alongside the database in AppData.  This prevents casual
    file-level snooping (SQLite viewers, plain text editors) but does NOT
    protect against an attacker with full read access to the user's AppData
    folder.  For stronger protection, wrap the key with Windows DPAPI
    (requires the pywin32 package).

Intentionally does NOT import from app_config to avoid circular imports.
"""
import os
import sys

from cryptography.fernet import Fernet, InvalidToken

from utils.logger import logger


# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------

def _get_key_path() -> str:
    """Resolve the key file path without importing app_config."""
    if sys.platform == "win32":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Clippie")
    else:
        base = os.path.expanduser("~/.clippie")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "clippie.key")


def _load_or_create_key() -> bytes:
    key_path = _get_key_path()
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(key_path, "wb") as f:
        f.write(key)
    logger.info("New encryption key generated and saved to: %s", key_path)
    return key


_fernet = Fernet(_load_or_create_key())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encrypt(text: str) -> str:
    """Encrypt a plaintext string and return a URL-safe base64 Fernet token."""
    return _fernet.encrypt(text.encode("utf-8")).decode("utf-8")


def decrypt(text: str) -> str:
    """
    Decrypt a Fernet token back to plaintext.

    Graceful fallback: if decryption fails (e.g. legacy plaintext rows that
    pre-date encryption, or wrong key), the original string is returned as-is.
    This ensures the UI remains functional while old rows are still visible.
    """
    try:
        return _fernet.decrypt(text.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        # Pre-encryption legacy data — return raw value unchanged
        return text
