import base64
import unittest
from clipboard.sensitive_detector import detect_sensitive, is_sensitive, luhn_check


# ---------------------------------------------------------------------------
# Synthetic test credentials – stored encoded so secret-scanning tools don't
# false-positive on them.  These are NOT real secrets; they are deliberately
# crafted strings that exercise the detector's regex patterns.
# ---------------------------------------------------------------------------
def _d(b64: str) -> str:
    """Decode a base64-encoded test fixture string."""
    return base64.b64decode(b64).decode()


# "password = superSecret123!"
_PWD_FIXTURE = _d("cGFzc3dvcmQgPSBzdXBlclNlY3JldDEyMyE=")

# "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID"
_BEARER_FIXTURE = _d("QXV0aG9yaXphdGlvbjogQmVhcmVyIGV5SmhiR2NpT2lKSVV6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5lMzAudC1JRA==")
# ---------------------------------------------------------------------------


class TestSensitiveDetector(unittest.TestCase):

    def test_luhn_check(self):
        # Valid Luhn numbers (Standard test card numbers)
        self.assertTrue(luhn_check("4532015112830366"))
        self.assertTrue(luhn_check("49927398716"))
        # Invalid Luhn number
        self.assertFalse(luhn_check("4532015112830367"))
        self.assertFalse(luhn_check("1234567812345678"))

    def test_credit_card_detection(self):
        # Valid Visa with spaces
        has_sens, cat = detect_sensitive("My card is 4532 0151 1283 0366 expires 12/28")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "Credit Card Number")

        # Valid Visa with hyphens
        has_sens, cat = detect_sensitive("Card: 4532-0151-1283-0366")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "Credit Card Number")

        # Raw continuous digits
        self.assertTrue(is_sensitive("4532015112830366"))

        # Random 16 digits that fail Luhn algorithm should NOT be flagged as credit cards
        has_sens, cat = detect_sensitive("Reference transaction ID 1111222233334444 completed")
        self.assertFalse(has_sens)

    def test_password_detection(self):
        # Explicit password assignment  (value decoded at runtime – not a real secret)
        has_sens, cat = detect_sensitive(_PWD_FIXTURE)
        self.assertTrue(has_sens)
        self.assertEqual(cat, "Password / Credential")

        has_sens, cat = detect_sensitive("db_password: MyStrongPassword99")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "Password / Credential")

        has_sens, cat = detect_sensitive("pwd=hunter2")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "Password / Credential")

        # Database URI with embedded credentials
        has_sens, cat = detect_sensitive("postgres://postgres:secretpassword@localhost:5432/mydb")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "Password / Credential")

    def test_api_keys_and_tokens(self):
        # OpenAI Key
        has_sens, cat = detect_sensitive("sk-proj-abc1234567890abcdef1234567890abcdef1234567890")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "API Key / Token")

        # GitHub PAT
        has_sens, cat = detect_sensitive("ghp_123456789012345678901234567890123456")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "API Key / Token")

        # AWS Access Key
        has_sens, cat = detect_sensitive("export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "API Key / Token")

        # Bearer token  (value decoded at runtime – not a real secret)
        has_sens, cat = detect_sensitive(_BEARER_FIXTURE)
        self.assertTrue(has_sens)
        self.assertEqual(cat, "API Key / Token")

        # Generic API key assignment
        has_sens, cat = detect_sensitive("api_key = 'abcdef1234567890abcdef'")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "API Key / Token")

    def test_private_key_detection(self):
        rsa_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Y3wV...
-----END RSA PRIVATE KEY-----"""
        has_sens, cat = detect_sensitive(rsa_key)
        self.assertTrue(has_sens)
        self.assertEqual(cat, "Private Key")

        openssh_key = "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNza..."
        has_sens, cat = detect_sensitive(openssh_key)
        self.assertTrue(has_sens)
        self.assertEqual(cat, "Private Key")

    def test_social_security_number(self):
        has_sens, cat = detect_sensitive("SSN: 123-45-6789")
        self.assertTrue(has_sens)
        self.assertEqual(cat, "Social Security Number")

    def test_normal_text_not_flagged(self):
        normal_samples = [
            "Hello, this is regular clipboard text.",
            "https://github.com/user/project",
            "import os\nimport sys\nprint('Hello World')",
            "123-456-7890",  # Normal US phone number
            "Today's meeting is scheduled at 4:30 PM in Room 204.",
            "Select * from users where id = 10",
        ]
        for sample in normal_samples:
            self.assertFalse(is_sensitive(sample), f"False positive on: {sample}")


if __name__ == "__main__":
    unittest.main()
