"""
Dedicated high-security encrypted vault storage for Clippie.

Stores sensitive items (passwords, credit cards, API keys, private keys, etc.)
in a separate, hardened encrypted file:
    AppData\Roaming\Clippie\vault.db.enc  (Windows)
    ~/.clippie/vault.db.enc                 (other platforms)

The entire file is encrypted with AES-256-GCM using keys protected by Windows DPAPI.
Opening or inspecting this file outside of Clippie reveals zero plaintext, no SQL
structure, and no metadata.
"""
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

from utils.encryption import (
    encrypt_gcm,
    decrypt_gcm,
    encrypt_with_passphrase,
    decrypt_with_passphrase
)
from utils.logger import logger


def get_vault_file_path() -> str:
    """Resolves the separate vault file path in AppData."""
    if sys.platform == 'win32':
        base = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Clippie')
    else:
        base = os.path.expanduser('~/.clippie')
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, 'vault.db.enc')


def get_vault_auth_path() -> str:
    """Resolves the separate vault auth file path in AppData."""
    if sys.platform == 'win32':
        base = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Clippie')
    else:
        base = os.path.expanduser('~/.clippie')
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, 'vault_auth.json')


def mask_sensitive_text(text: str, category: str = '') -> str:
    """Generates a shoulder-surfing safe masked preview of sensitive text."""
    if not text:
        return ''
    cat = (category or '').lower()
    if 'card' in cat:
        digits = re.sub(r'\D', '', text)
        if len(digits) >= 4:
            return f'•••• •••• •••• {digits[-4:]}'
        return '•••• •••• •••• ••••'
    if 'password' in cat or 'credential' in cat:
        return '••••••••••••'
    if 'key' in cat or 'token' in cat:
        if len(text) > 8:
            return f'{text[:3]}••••••••{text[-3:]}'
        return '••••••••'
    # Default masking
    if len(text) > 6:
        return f'{text[:2]}••••••••{text[-2:]}'
    return '••••••••'


class VaultStorage:
    def __init__(self, file_path: Optional[str] = None, auth_path: Optional[str] = None):
        self.file_path = file_path or get_vault_file_path()
        self.auth_path = auth_path or get_vault_auth_path()

    def _read_raw(self) -> List[Dict[str, Any]]:
        """Reads and decrypts the separate vault file. Returns list of item dicts."""
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'rb') as f:
                encrypted_payload = f.read()
            if not encrypted_payload:
                return []
            decrypted_bytes = decrypt_gcm(encrypted_payload)
            data = json.loads(decrypted_bytes.decode('utf-8'))
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error('Failed to read encrypted vault file: %s', e, exc_info=True)
            return []

    def _write_raw(self, items: List[Dict[str, Any]]) -> bool:
        """Encrypts and atomically writes items to the separate vault file."""
        temp_path = self.file_path + '.tmp'
        try:
            raw_bytes = json.dumps(items, ensure_ascii=False, indent=2).encode('utf-8')
            encrypted_payload = encrypt_gcm(raw_bytes)

            with open(temp_path, 'wb') as f:
                f.write(encrypted_payload)
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace
            if os.path.exists(self.file_path):
                os.replace(temp_path, self.file_path)
            else:
                os.rename(temp_path, self.file_path)
            return True
        except Exception as e:
            logger.error('Failed to write encrypted vault file: %s', e, exc_info=True)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            return False

    def add_item(self, content: str, category: str = 'Sensitive Data', label: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Adds an item to the separate encrypted vault.
        Deduplicates against the immediate previous entry if content is identical.
        """
        if not content or not content.strip():
            return None

        items = self._read_raw()
        # Avoid duplicate consecutive additions
        if items and items[0].get('content') == content:
            return items[0]

        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        new_item = {
            'id': str(uuid.uuid4()),
            'category': category or 'Sensitive Data',
            'content': content,
            'masked': mask_sensitive_text(content, category),
            'label': label or category or 'Secure Item',
            'timestamp': now_str,
            'is_favorite': 0
        }
        # Prepend so newest is first
        items.insert(0, new_item)
        if self._write_raw(items):
            logger.info('Saved sensitive item to encrypted vault (category: %s)', category)
            return new_item
        return None

    def get_items(self, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all decrypted items from the vault, optionally filtered."""
        items = self._read_raw()
        if not search_query or not search_query.strip():
            return items
        needle = search_query.strip().lower()
        matched = []
        for item in items:
            cat = str(item.get('category', '')).lower()
            label = str(item.get('label', '')).lower()
            content = str(item.get('content', '')).lower()
            ts = str(item.get('timestamp', '')).lower()
            if needle in cat or needle in label or needle in content or needle in ts:
                matched.append(item)
        return matched

    def get_count(self) -> int:
        """Returns the number of items stored in the separate vault."""
        return len(self._read_raw())

    def delete_item(self, item_id: str) -> bool:
        """Removes an item from the vault by its ID."""
        items = self._read_raw()
        initial_len = len(items)
        items = [i for i in items if str(i.get('id')) != str(item_id)]
        if len(items) != initial_len:
            return self._write_raw(items)
        return False

    def clear(self) -> bool:
        """Wipes all data in the separate vault file."""
        return self._write_raw([])

    def export_to_file(self, target_filepath: str, passphrase: str) -> int:
        """
        Exports all vault records into a separate password-protected file
        encrypted with PBKDF2-HMAC-SHA256 + AES-256-GCM.
        """
        items = self._read_raw()
        payload = json.dumps(items, ensure_ascii=False).encode('utf-8')
        enc_bytes = encrypt_with_passphrase(payload, passphrase)
        with open(target_filepath, 'wb') as f:
            f.write(enc_bytes)
        logger.info('Exported %d vault items to %s', len(items), target_filepath)
        return len(items)

    def import_from_file(self, source_filepath: str, passphrase: str) -> int:
        """
        Imports records from a password-protected export file and merges into the vault.
        """
        with open(source_filepath, 'rb') as f:
            enc_bytes = f.read()
        dec_bytes = decrypt_with_passphrase(enc_bytes, passphrase)
        imported_items = json.loads(dec_bytes.decode('utf-8'))
        if not isinstance(imported_items, list):
            raise ValueError('Invalid import payload: expected list.')

        current_items = self._read_raw()
        existing_ids = {str(i.get('id')) for i in current_items}
        added_count = 0
        for item in imported_items:
            if str(item.get('id')) not in existing_ids:
                current_items.append(item)
                existing_ids.add(str(item.get('id')))
                added_count += 1

        # Sort by timestamp descending
        current_items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        self._write_raw(current_items)
        logger.info('Imported %d new vault items from %s', added_count, source_filepath)
        return added_count

    def is_password_set(self) -> bool:
        """Returns True if a master password has been configured for the vault."""
        if not os.path.exists(self.auth_path):
            return False
        try:
            with open(self.auth_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return bool(data.get('hash') and data.get('salt'))
        except Exception:
            return False

    def set_password(self, password: str) -> bool:
        """Configures a new salted PBKDF2-HMAC-SHA256 password for the vault."""
        if not password:
            return False
        import hashlib
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()
        try:
            with open(self.auth_path, 'w', encoding='utf-8') as f:
                json.dump({'salt': salt.hex(), 'hash': pwd_hash}, f)
            logger.info("Configured master password for Secure Vault.")
            return True
        except Exception as e:
            logger.error("Failed to set vault password: %s", e)
            return False

    def verify_password(self, password: str) -> bool:
        """Verifies whether the provided password matches the configured vault password."""
        if not os.path.exists(self.auth_path):
            return False
        try:
            with open(self.auth_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            salt = bytes.fromhex(data['salt'])
            expected_hash = data['hash']
            import hashlib
            actual_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()
            return actual_hash == expected_hash
        except Exception as e:
            logger.error("Failed to verify vault password: %s", e)
            return False


# Global singleton instance
vault = VaultStorage()

_vault_unlocked_in_session = False


def is_vault_password_set() -> bool:
    return vault.is_password_set()


def set_vault_password(password: str) -> bool:
    return vault.set_password(password)


def verify_vault_password(password: str) -> bool:
    return vault.verify_password(password)


def is_vault_unlocked() -> bool:
    global _vault_unlocked_in_session
    return _vault_unlocked_in_session


def unlock_vault():
    global _vault_unlocked_in_session
    _vault_unlocked_in_session = True


def lock_vault():
    global _vault_unlocked_in_session
    _vault_unlocked_in_session = False


def add_vault_item(content: str, category: str = 'Sensitive Data', label: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return vault.add_item(content, category, label)


def get_vault_items(search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    return vault.get_items(search_query)


def get_vault_count() -> int:
    return vault.get_count()


def delete_vault_item(item_id: str) -> bool:
    return vault.delete_item(item_id)


def clear_vault() -> bool:
    return vault.clear()


def export_vault(target_path: str, passphrase: str) -> int:
    return vault.export_to_file(target_path, passphrase)


def import_vault(source_path: str, passphrase: str) -> int:
    return vault.import_from_file(source_path, passphrase)
