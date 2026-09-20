import pyperclip
import re
import time
import os
import hashlib
import ctypes
from PIL import ImageGrab
from db.database import add_item
from app_config import get_writable_path
from utils.logger import logger
from clipboard.sensitive_detector import detect_sensitive, is_sensitive
from utils.notifier import notifier

last_ui_copy = None
last_ui_image_hash = None


def get_clipboard_sequence():
    """Returns the Windows clipboard sequence number, or None on other platforms."""
    try:
        if os.name == 'nt':
            return ctypes.windll.user32.GetClipboardSequenceNumber()
    except Exception:
        pass
    return None


class ClipboardMonitor:
    def __init__(self):
        self.last_clipboard = ""
        self.last_image_hash = ""
        self.is_paused = False
        self.last_sequence = get_clipboard_sequence()

    def run(self):
        global last_ui_copy, last_ui_image_hash
        logger.info("Clipboard monitor started.")

        image_dir = get_writable_path("images")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        while True:
            try:
                if getattr(self, 'is_paused', False):
                    time.sleep(0.3)
                    continue

                current_sequence = get_clipboard_sequence()
                # On Windows, if sequence hasn't changed, no new copy event occurred
                if current_sequence is not None and self.last_sequence is not None:
                    if current_sequence == self.last_sequence:
                        time.sleep(0.25)
                        continue

                # 1. Check for image
                img = ImageGrab.grabclipboard()
                if img is not None and hasattr(img, 'save'):
                    # Convert to RGB so we can save as PNG
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    img_byte_arr = img.tobytes()
                    img_hash = hashlib.sha256(img_byte_arr).hexdigest()

                    if img_hash != self.last_image_hash:
                        if img_hash == last_ui_image_hash:
                            self.last_image_hash = img_hash
                            if current_sequence is not None:
                                self.last_sequence = current_sequence
                            time.sleep(0.3)
                            continue

                        filename = f"img_{img_hash}.png"
                        filepath = os.path.join(image_dir, filename)
                        img.save(filepath, "PNG")

                        add_item(filepath, manual_tag="Image")
                        self.last_image_hash = img_hash
                        self.last_clipboard = ""  # clear text check

                    if current_sequence is not None:
                        self.last_sequence = current_sequence
                    time.sleep(0.3)
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
                    if current_sequence is not None:
                        self.last_sequence = current_sequence
                    time.sleep(0.3)
                    continue

                # 2. Check for text
                text = pyperclip.paste()
                if text:
                    if text == last_ui_copy:
                        self.last_clipboard = text
                        if current_sequence is not None:
                            self.last_sequence = current_sequence
                        time.sleep(0.3)
                        continue

                    # Security: check for sensitive patterns
                    has_sensitive, sensitive_type = detect_sensitive(text)
                    if has_sensitive:
                        category = sensitive_type or "Sensitive Data"
                        logger.info("Sensitive content detected (%s) — routing to separate encrypted vault.", category)
                        self.last_clipboard = text
                        if current_sequence is not None:
                            self.last_sequence = current_sequence

                        # Save to isolated encrypted vault file (never saved to normal clipboard.db)
                        from utils.vault_storage import add_vault_item
                        add_vault_item(text, category=category)

                        # Always emit notification, even if the user copied the exact same sensitive item again
                        notifier.emit_sensitive(
                            category,
                            f"Detected {category}. Saved securely to encrypted Vault file."
                        )
                        time.sleep(0.3)
                        continue

                    if text != self.last_clipboard:
                        add_item(text)
                        self.last_clipboard = text
                        self.last_image_hash = ""  # clear image check

                if current_sequence is not None:
                    self.last_sequence = current_sequence

                time.sleep(0.3)
            except Exception as e:
                # High fix #4: log exceptions instead of silently discarding them
                logger.error("Clipboard monitor error: %s", e, exc_info=True)
                time.sleep(0.3)
