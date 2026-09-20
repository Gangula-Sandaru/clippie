import re
from typing import Tuple, Optional


def luhn_check(number_str: str) -> bool:
    """
    Validate a number string using Luhn algorithm (mod 10).
    Ensures card numbers are mathematically valid, avoiding false positives.
    """
    digits = [int(d) for d in number_str if d.isdigit()]
    if len(digits) < 2:
        return False

    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


def is_valid_card_number(raw_digits: str) -> bool:
    """
    Check if digits match known credit/debit card IIN/BIN prefixes and pass Luhn checksum.
    Supported: Visa, Mastercard, American Express, Discover, Diners Club, JCB.
    """
    length = len(raw_digits)
    if length not in (13, 14, 15, 16, 19):
        return False

    if not luhn_check(raw_digits):
        return False

    # Visa: begins with 4 (13, 16, 19 digits)
    if raw_digits.startswith('4') and length in (13, 16, 19):
        return True

    # Mastercard: 51-55 or 2221-2720 (16 digits)
    if length == 16:
        prefix2 = int(raw_digits[:2])
        prefix4 = int(raw_digits[:4])
        if (51 <= prefix2 <= 55) or (2221 <= prefix4 <= 2720):
            return True

    # American Express: 34 or 37 (15 digits)
    if length == 15 and (raw_digits.startswith('34') or raw_digits.startswith('37')):
        return True

    # Discover: 6011, 65, 644-649, 622126-622925 (16 or 19 digits)
    if length in (16, 19):
        if raw_digits.startswith('6011') or raw_digits.startswith('65'):
            return True
        prefix3 = int(raw_digits[:3])
        if 644 <= prefix3 <= 649:
            return True
        prefix6 = int(raw_digits[:6])
        if 622126 <= prefix6 <= 622925:
            return True

    # Diners Club: 300-305, 36, 38 (14 digits)
    if length == 14:
        if raw_digits.startswith(('36', '38')) or (300 <= int(raw_digits[:3]) <= 305):
            return True

    # JCB: 3528-3589 (16 to 19 digits)
    if length in (16, 19) and (3528 <= int(raw_digits[:4]) <= 3589):
        return True

    return False


# Potential card candidate regex (groups of 4 or 13-19 continuous digits)
_CARD_CANDIDATE_REGEX = re.compile(
    r'\b(?:\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{1,7}|\d{13,19})\b'
)

# Password and credential patterns
_PASSWORD_PATTERNS = [
    # Explicit password assignments: password: xyz, pwd=xyz, password="xyz"
    re.compile(r'(?i)\b(?:password|passwd|pwd|db_password|api_secret)\s*[:=]\s*["\']?(\S+?)["\']?(?:\s|$)'),
    # Connection string / URI with credentials: e.g. postgres://user:password@hostname:5432
    re.compile(r'(?i)\b[a-zA-Z][a-zA-Z0-9+.-]*://[^:\s/]+:([^@\s/]+)@'),
]

# API Keys and authentication tokens
_API_KEY_PATTERNS = [
    # OpenAI API Keys
    re.compile(r'\bsk-(?:proj-|live-)?[a-zA-Z0-9_\-]{20,}\b'),
    # GitHub Tokens (Personal Access Token, OAuth, App Token)
    re.compile(r'\bgh[pousr]_[A-Za-z0-9_]{36,}\b'),
    # AWS Access Key ID
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    # AWS Secret Key assignment
    re.compile(r'(?i)aws_secret_access_key\s*[:=]\s*["\']?[A-Za-z0-9/+=]{40}["\']?'),
    # Google API Key
    re.compile(r'\bAIza[0-9A-Za-z\-_]{35}\b'),
    # Slack Bot / User Token
    re.compile(r'\bxox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}\b'),
    # Stripe API Secret / Restricted Key
    re.compile(r'\b(?:sk|rk)_(?:live|test)_[0-9a-zA-Z]{24,}\b'),
    # Bearer Token
    re.compile(r'(?i)\bBearer\s+[a-zA-Z0-9_\-\.]{25,}\b'),
    # Generic API Key / Secret assignments
    re.compile(r'(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?token)\s*[:=]\s*["\']?[a-zA-Z0-9_\-\.]{16,}["\']?'),
]

# Private keys & certificates
_PRIVATE_KEY_PATTERNS = [
    re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----'),
    re.compile(r'-----BEGIN PGP PRIVATE KEY BLOCK-----'),
]

# Personal Identifiers (e.g. US Social Security Number)
_PII_PATTERNS = [
    re.compile(r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b'),
]


def detect_sensitive(text: str) -> Tuple[bool, Optional[str]]:
    """
    Analyzes text to detect sensitive information.
    
    Returns:
        Tuple[bool, Optional[str]]: (True, category_name) if sensitive content is found,
                                     (False, None) otherwise.
    """
    if not text or not isinstance(text, str):
        return False, None

    # Check for Private Keys first (high severity)
    for pattern in _PRIVATE_KEY_PATTERNS:
        if pattern.search(text):
            return True, "Private Key"

    # Check for Credit / Debit Card numbers with Luhn and IIN verification
    for match in _CARD_CANDIDATE_REGEX.finditer(text):
        raw_digits = re.sub(r'\D', '', match.group(0))
        if is_valid_card_number(raw_digits):
            return True, "Credit Card Number"

    # Check for Passwords / Credentials
    for pattern in _PASSWORD_PATTERNS:
        if pattern.search(text):
            return True, "Password / Credential"

    # Check for API Keys & Tokens
    for pattern in _API_KEY_PATTERNS:
        if pattern.search(text):
            return True, "API Key / Token"

    # Check for PII (e.g. SSN)
    for pattern in _PII_PATTERNS:
        if pattern.search(text):
            return True, "Social Security Number"

    return False, None


def is_sensitive(text: str) -> bool:
    """
    Convenience wrapper returning True if text contains any sensitive data.
    """
    has_sensitive, _ = detect_sensitive(text)
    return has_sensitive
