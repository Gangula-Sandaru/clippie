import os
import shutil
import tempfile
import unittest

from utils.encryption import (
    encrypt,
    decrypt,
    encrypt_gcm,
    decrypt_gcm,
    encrypt_with_passphrase,
    decrypt_with_passphrase,
    is_dpapi_active,
    dpapi_protect,
    dpapi_unprotect
)
from utils.vault_storage import VaultStorage, mask_sensitive_text


class TestEncryptionAndVault(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.vault_file = os.path.join(self.test_dir, "test_vault.db.enc")
        self.auth_file = os.path.join(self.test_dir, "test_vault_auth.json")
        self.vault = VaultStorage(self.vault_file, self.auth_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dpapi_roundtrip(self):
        """Verify Windows DPAPI key protection works without error."""
        if is_dpapi_active():
            raw_data = b"confidential-key-256-bit-data-bytes"
            protected = dpapi_protect(raw_data)
            self.assertNotEqual(protected, raw_data)
            unprotected = dpapi_unprotect(protected)
            self.assertEqual(unprotected, raw_data)

    def test_aes_gcm_authenticated_encryption(self):
        """AES-256-GCM should encrypt, decrypt, and reject tampered payloads."""
        payload = b"super-secret-password-xyz-999"
        encrypted = encrypt_gcm(payload)
        self.assertGreater(len(encrypted), len(payload) + 12)

        # Decrypt roundtrip
        decrypted = decrypt_gcm(encrypted)
        self.assertEqual(decrypted, payload)

        # Tamper detection: flip a bit in ciphertext
        tampered = bytearray(encrypted)
        tampered[-1] ^= 0x01
        with self.assertRaises(Exception):
            decrypt_gcm(bytes(tampered))

    def test_passphrase_export_import(self):
        """Passphrase derivation must decrypt only with correct password."""
        raw = b'{"items": ["secret_token_abc"]}'
        pwd = "CorrectMasterPass123!"

        encrypted_file = encrypt_with_passphrase(raw, pwd)
        self.assertTrue(encrypted_file.startswith(b"CLPVLT01"))

        # Correct password succeeds
        decrypted = decrypt_with_passphrase(encrypted_file, pwd)
        self.assertEqual(decrypted, raw)

        # Wrong password raises error
        with self.assertRaises(Exception):
            decrypt_with_passphrase(encrypted_file, "WrongPassword!")

    def test_separate_vault_file_is_completely_encrypted_on_disk(self):
        """Verify that items saved to the vault file leave ZERO plaintext on disk."""
        secret_pass = "UltraSecretApiKey-987654321"
        secret_card = "4532 0151 1283 0366"

        self.vault.add_item(secret_pass, category="Password / Credential")
        self.vault.add_item(secret_card, category="Credit Card Number")

        self.assertEqual(self.vault.get_count(), 2)
        self.assertTrue(os.path.exists(self.vault_file))

        # Inspect raw bytes on disk
        with open(self.vault_file, "rb") as f:
            disk_bytes = f.read()

        # Critical security check: No plain text passwords, cards, or SQL strings on disk
        self.assertNotIn(b"UltraSecretApiKey", disk_bytes)
        self.assertNotIn(b"987654321", disk_bytes)
        self.assertNotIn(b"4532 0151", disk_bytes)
        self.assertNotIn(b"Password / Credential", disk_bytes)
        self.assertNotIn(b"sqlite", disk_bytes.lower())

    def test_vault_masking(self):
        """Masking must protect secrets from shoulder-surfing."""
        card_mask = mask_sensitive_text("4532015112830366", "Credit Card Number")
        self.assertTrue(card_mask.endswith("0366"))
        self.assertIn("••••", card_mask)

        pass_mask = mask_sensitive_text("SuperSecretPass!", "Password / Credential")
        self.assertEqual(pass_mask, "••••••••••••")

    def test_vault_delete_and_clear(self):
        """Test deleting individual items and wiping the vault."""
        item1 = self.vault.add_item("token_1", category="API Key / Token")
        item2 = self.vault.add_item("token_2", category="API Key / Token")
        self.assertEqual(self.vault.get_count(), 2)

        self.vault.delete_item(item1["id"])
        self.assertEqual(self.vault.get_count(), 1)
        remaining = self.vault.get_items()
        self.assertEqual(remaining[0]["id"], item2["id"])

        self.vault.clear()
        self.assertEqual(self.vault.get_count(), 0)

    def test_vault_export_and_import_files(self):
        """Test exporting vault to a separate file and importing back."""
        self.vault.add_item("ghp_secretGithubToken1234567890", category="API Key / Token")
        self.vault.add_item("password=dbPasswordAdmin99", category="Password / Credential")

        export_path = os.path.join(self.test_dir, "export.clpvlt")
        pwd = "ExportSecurePassphrase!456"
        count = self.vault.export_to_file(export_path, pwd)
        self.assertEqual(count, 2)
        self.assertTrue(os.path.exists(export_path))

        # Import into a second fresh vault
        vault2_file = os.path.join(self.test_dir, "vault2.db.enc")
        vault2 = VaultStorage(vault2_file)
        self.assertEqual(vault2.get_count(), 0)

        imported_count = vault2.import_from_file(export_path, pwd)
        self.assertEqual(imported_count, 2)
        self.assertEqual(vault2.get_count(), 2)

    def test_vault_password_management(self):
        """Test setting, hashing, and verifying vault master password."""
        # 1. Not set initially
        self.assertFalse(self.vault.is_password_set())

        # 2. Set password
        pwd = "MySuperSecretVaultPassword!999"
        self.assertTrue(self.vault.set_password(pwd))
        self.assertTrue(self.vault.is_password_set())

        # 3. Check file is hashed, not plain text
        with open(self.auth_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn(pwd, content)
        self.assertIn("hash", content)
        self.assertIn("salt", content)

        # 4. Verification
        self.assertTrue(self.vault.verify_password(pwd))
        self.assertFalse(self.vault.verify_password("IncorrectPassword!"))
        self.assertFalse(self.vault.verify_password(""))


if __name__ == "__main__":
    unittest.main()
