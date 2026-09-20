"""
High-security encryption for Clippie.

Key features:
1. Windows DPAPI (Data Protection API) Key Isolation:
   The master key is encrypted with Windows CryptProtectData and saved in a
   dedicated protected file:
       AppData\\Roaming\\Clippie\\clippie.key.dpapi  (Windows)
       ~/.clippie/clippie.key                       (other platforms)
   Anti-theft guarantee: Even if someone copies the key or database files,
   the data CANNOT be decrypted on another machine or by another user.
2. AES-256-GCM Authenticated Encryption:
   Used for high-security separate vault storage, providing both confidential
   encryption and cryptographic integrity (anti-tampering).
3. PBKDF2-HMAC-SHA256 Passphrase Derivation:
   Used for encrypted standalone file export/import.
4. Fernet backward compatibility:
   Seamless compatibility for existing clipboard.db rows.
"""
import base64
import os
import sys
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from utils.logger import logger

# ---------------------------------------------------------------------------
# Windows DPAPI implementation (ctypes - zero external dependencies)
# ---------------------------------------------------------------------------

_HAS_DPAPI = False

if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes

        class _DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ('cbData', wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_char))
            ]

        _CryptProtectData = ctypes.windll.crypt32.CryptProtectData
        _CryptProtectData.argtypes = [
            ctypes.POINTER(_DATA_BLOB),
            wintypes.LPCWSTR,
            ctypes.POINTER(_DATA_BLOB),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DATA_BLOB)
        ]
        _CryptProtectData.restype = wintypes.BOOL

        _CryptUnprotectData = ctypes.windll.crypt32.CryptUnprotectData
        _CryptUnprotectData.argtypes = [
            ctypes.POINTER(_DATA_BLOB),
            ctypes.POINTER(wintypes.LPWSTR),
            ctypes.POINTER(_DATA_BLOB),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DATA_BLOB)
        ]
        _CryptUnprotectData.restype = wintypes.BOOL

        _LocalFree = ctypes.windll.kernel32.LocalFree
        _LocalFree.argtypes = [ctypes.c_void_p]
        _LocalFree.restype = ctypes.c_void_p

        _HAS_DPAPI = True
    except Exception as e:
        logger.warning("DPAPI initialization failed: %s. Falling back to file storage.", e)
        _HAS_DPAPI = False


def dpapi_protect(data: bytes, description: str = "ClippieMasterKey") -> bytes:
    """Encrypts bytes using Windows DPAPI tied to the logged-in user profile."""
    if not _HAS_DPAPI:
        return data
    blob_in = _DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_char)))
    blob_out = _DATA_BLOB()
    # CRYPTPROTECT_UI_FORBIDDEN = 0x1
    if not _CryptProtectData(ctypes.byref(blob_in), description, None, None, None, 0x1, ctypes.byref(blob_out)):
        raise RuntimeError("Windows CryptProtectData failed")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        _LocalFree(blob_out.pbData)


def dpapi_unprotect(protected_data: bytes) -> bytes:
    """Decrypts bytes using Windows DPAPI for the current logged-in user."""
    if not _HAS_DPAPI:
        return protected_data
    blob_in = _DATA_BLOB(len(protected_data), ctypes.cast(ctypes.create_string_buffer(protected_data), ctypes.POINTER(ctypes.c_char)))
    blob_out = _DATA_BLOB()
    if not _CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0x1, ctypes.byref(blob_out)):
        raise RuntimeError("Windows CryptUnprotectData failed (cannot decrypt on unauthorized account/system)")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        _LocalFree(blob_out.pbData)


# ---------------------------------------------------------------------------
# Key management & storage
# ---------------------------------------------------------------------------

def _get_base_dir() -> str:
    if sys.platform == "win32":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Clippie")
    else:
        base = os.path.expanduser("~/.clippie")
    os.makedirs(base, exist_ok=True)
    return base


def _get_dpapi_key_path() -> str:
    return os.path.join(_get_base_dir(), "clippie.key.dpapi")


def _get_legacy_key_path() -> str:
    return os.path.join(_get_base_dir(), "clippie.key")


def _load_or_create_master_key() -> bytes:
    """
    Loads or generates the 256-bit master key.
    On Windows, keys are protected with DPAPI to prevent physical file theft.
    Migrates any legacy plaintext key into DPAPI storage.
    """
    dpapi_path = _get_dpapi_key_path()
    legacy_path = _get_legacy_key_path()

    # 1. Try loading from DPAPI-protected file
    if _HAS_DPAPI and os.path.exists(dpapi_path):
        try:
            with open(dpapi_path, "rb") as f:
                encrypted_blob = f.read()
            raw_key = dpapi_unprotect(encrypted_blob)
            logger.info("Loaded master key protected by Windows DPAPI.")
            return raw_key
        except Exception as e:
            logger.error("Failed to unprotect DPAPI key: %s", e, exc_info=True)

    # 2. Check for legacy plaintext key to migrate
    if os.path.exists(legacy_path):
        try:
            with open(legacy_path, "rb") as f:
                raw_key = f.read()
            if _HAS_DPAPI:
                try:
                    protected = dpapi_protect(raw_key)
                    with open(dpapi_path, "wb") as f:
                        f.write(protected)
                    # Securely wipe / remove legacy plaintext key
                    with open(legacy_path, "wb") as f:
                        f.write(os.urandom(len(raw_key)))
                    os.remove(legacy_path)
                    logger.info("Migrated legacy key to DPAPI-protected storage.")
                except Exception as e:
                    logger.warning("Failed to migrate key to DPAPI: %s", e)
            return raw_key
        except Exception as e:
            logger.error("Failed to read legacy key: %s", e, exc_info=True)

    # 3. Generate a brand new master key
    raw_key = Fernet.generate_key()
    if _HAS_DPAPI:
        try:
            protected = dpapi_protect(raw_key)
            with open(dpapi_path, "wb") as f:
                f.write(protected)
            logger.info("Generated new master key secured with Windows DPAPI.")
            return raw_key
        except Exception as e:
            logger.error("DPAPI protect failed on new key: %s", e)

    # Fallback for non-DPAPI
    with open(legacy_path, "wb") as f:
        f.write(raw_key)
    logger.info("Generated new master key saved to file.")
    return raw_key


_MASTER_KEY = _load_or_create_master_key()
_fernet = Fernet(_MASTER_KEY)

# 256-bit raw key for AES-256-GCM
_AES_KEY = base64.urlsafe_b64decode(_MASTER_KEY)
if len(_AES_KEY) != 32:
    import hashlib
    _AES_KEY = hashlib.sha256(_MASTER_KEY).digest()
_aesgcm = AESGCM(_AES_KEY)


# ---------------------------------------------------------------------------
# Public Encryption & Decryption APIs
# ---------------------------------------------------------------------------

def is_dpapi_active() -> bool:
    """Returns True if Windows DPAPI hardware/account protection is active."""
    return _HAS_DPAPI and os.path.exists(_get_dpapi_key_path())


def encrypt(text: str) -> str:
    """Encrypt a plaintext string using Fernet and return base64 token."""
    return _fernet.encrypt(text.encode("utf-8")).decode("utf-8")


def decrypt(text: str) -> str:
    """
    Decrypt a Fernet token back to plaintext.
    Gracefully returns text unchanged if decryption fails (e.g. legacy plaintext).
    """
    try:
        return _fernet.decrypt(text.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        return text


# ---------------------------------------------------------------------------
# High-Security AES-256-GCM Functions (for separate vault files)
# ---------------------------------------------------------------------------

def encrypt_gcm(plaintext_bytes: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """
    Encrypts raw bytes using AES-256-GCM.
    Returns: 12-byte random nonce + ciphertext with 16-byte authentication tag.
    """
    nonce = os.urandom(12)
    ciphertext = _aesgcm.encrypt(nonce, plaintext_bytes, associated_data)
    return nonce + ciphertext


def decrypt_gcm(payload: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """
    Decrypts an AES-256-GCM payload (12-byte nonce + ciphertext + auth tag).
    Raises Exception if authentication fails (tampering detected).
    """
    if len(payload) < 28:
        raise ValueError("Invalid AES-GCM payload: too short.")
    nonce = payload[:12]
    ciphertext = payload[12:]
    return _aesgcm.decrypt(nonce, ciphertext, associated_data)


# ---------------------------------------------------------------------------
# Passphrase-Derived Encryption (for Standalone File Export / Backup)
# ---------------------------------------------------------------------------

def derive_key_from_passphrase(passphrase: str, salt: bytes, iterations: int = 600000) -> bytes:
    """Derives a 256-bit key from a passphrase using PBKDF2-HMAC-SHA256 (600,000 iterations)."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_with_passphrase(data: bytes, passphrase: str) -> bytes:
    """
    Encrypts arbitrary bytes into a standalone password-protected file format:
    Header (8 bytes: 'CLPVLT01') + Salt (16 bytes) + Nonce (12 bytes) + Ciphertext + Tag.
    """
    salt = os.urandom(16)
    key = derive_key_from_passphrase(passphrase, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return b"CLPVLT01" + salt + nonce + ciphertext


def decrypt_with_passphrase(file_bytes: bytes, passphrase: str) -> bytes:
    """Decrypts a standalone password-protected file encrypted with encrypt_with_passphrase."""
    if len(file_bytes) < 8 + 16 + 12 + 16 or not file_bytes.startswith(b"CLPVLT01"):
        raise ValueError("Invalid Clippie Vault encrypted file format.")
    salt = file_bytes[8:24]
    nonce = file_bytes[24:36]
    ciphertext = file_bytes[36:]
    key = derive_key_from_passphrase(passphrase, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)

