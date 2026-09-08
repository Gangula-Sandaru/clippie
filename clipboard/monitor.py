import pyperclip
import re
import time
import os
import hashlib
from PIL import ImageGrab
from db.database import add_item
from app_config import get_writable_path
from utils.logger import logger

last_ui_copy = None
last_ui_image_hash = None

# ---------------------------------------------------------------------------
# Sensitive-content filter (Critical fix #2)
# ---------------------------------------------------------------------------
_SENSITIVE_PATTERNS = [
    # Credit / debit card numbers — Visa, Mastercard, Amex, Discover
    re.compile(
        r'\b(?:'
        r'4[0-9]{12}(?:[0-9]{3})?'           # Visa (13 or 16 digits)
        r'|5[1-5][0-9]{14}'                   # Mastercard
        r'|3[47][0-9]{13}'                    # American Express
        r'|6(?:011|5[0-9]{2})[0-9]{12}'      # Discover
        r')\b'
    ),
    # PEM / OpenSSH private key headers
    re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----'),
    re.compile(r'-----BEGIN PGP PRIVATE KEY BLOCK-----'),
]


def is_sensitive(text: str) -> bool:
    """
    Return True if the text matches any known sensitive-data pattern.
    Content flagged here is NOT saved to the clipboard history database.
    """
    for pattern in _SENSITIVE_PATTERNS:
        if pattern.search(text):
            return True
    return False


class ClipboardMonitor:
    def __init__(self):
        self.last_clipboard = ""
        self.last_image_hash = ""
        self.is_paused = False

    def run(self):
        global last_ui_copy, last_ui_image_hash
        logger.info("Clipboard monitor started.")

        image_dir = get_writable_path("images")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        while True:
            try:
                if getattr(self, 'is_paused', False):
                    time.sleep(0.5)
                    continue

                # 1. Check for image
                img = ImageGrab.grabclipboard()
                if img is not None and hasattr(img, 'save'):
                    # Convert to RGB so we can save as PNG
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    img_byte_arr = img.tobytes()
                    # SHA-256 instead of MD5 (Medium fix #7)
                    img_hash = hashlib.sha256(img_byte_arr).hexdigest()

                    if img_hash != self.last_image_hash:
                        if img_hash == last_ui_image_hash:
                            self.last_image_hash = img_hash
                            time.sleep(0.5)
                            continue

                        filename = f"img_{img_hash}.png"
                        filepath = os.path.join(image_dir, filename)
                        img.save(filepath, "PNG")

                        add_item(filepath, manual_tag="Image")
                        self.last_image_hash = img_hash
                        self.last_clipboard = ""  # clear text check

                    time.sleep(0.5)
                    continue
                elif isinstance(img, list) and len(img) > 0:
                    # File(s) copied (path list), not image data directly
                    for file_path in img:
                        if isinstance(file_path, str) and file_path.lower().endswith(
                                ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.ico')):
                            if file_path != self.last_clipboard:
                                add_item(file_path, manual_tag="Image")
                                self.last_clipboard = file_path
                                self.last_image_hash = ""  # clear image data check
                    time.sleep(0.5)
                    continue

                # 2. Check for text
                text = pyperclip.paste()
                if text and text != self.last_clipboard:
                    if text == last_ui_copy:
                        self.last_clipboard = text
                        continue

                    # Security: skip content matching sensitive patterns
                    if is_sensitive(text):
                        logger.info("Sensitive content detected — skipping history save.")
                        self.last_clipboard = text
                        time.sleep(0.5)
                        continue

                    add_item(text)
                    self.last_clipboard = text
                    self.last_image_hash = ""  # clear image check

                time.sleep(0.5)
            except Exception as e:
                # High fix #4: log exceptions instead of silently discarding them
                logger.error("Clipboard monitor error: %s", e, exc_info=True)
                time.sleep(0.5)
