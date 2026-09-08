import hashlib
import json
import os
import sys

from utils.logger import logger


def get_writable_path(filename):
    """Redirects files to the user's AppData folder for Windows compatibility."""
    if sys.platform == "win32":
        # Points to C:\Users\Name\AppData\Roaming\Clippie
        base_path = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Clippie")
    else:
        base_path = os.path.expanduser("~/.clippie")

    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
    return os.path.join(base_path, filename)


class ConfigManager:
    def __init__(self):
        self.config_path = get_writable_path("config.json")
        self.sig_path = get_writable_path("config.json.sig")
        self.defaults = {
            "theme": "Dark OLED",
            "history_limit": "100 Records",
            "startup": True,
            "hotkey": "alt",
            "first_run": True,
            "floating_widget": True,
            "cloud_sync": False
        }
        self.settings = self.load_settings()

    def _calculate_checksum(self, data_bytes: bytes) -> str:
        return hashlib.sha256(data_bytes).hexdigest()

    def load_settings(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'rb') as f:
                    content = f.read()

                # Verify checksum if signature file exists
                if os.path.exists(self.sig_path):
                    with open(self.sig_path, 'r', encoding='utf-8') as sf:
                        expected_hash = sf.read().strip()
                    actual_hash = self._calculate_checksum(content)
                    if actual_hash != expected_hash:
                        logger.warning(
                            "Config integrity check failed! Expected %s, got %s. Falling back to defaults.",
                            expected_hash, actual_hash
                        )
                        return dict(self.defaults)

                loaded = json.loads(content.decode('utf-8'))
                return {**self.defaults, **loaded}
            except Exception as e:
                logger.error("Failed to load config: %s. Using default settings.", e, exc_info=True)
                return dict(self.defaults)
        return dict(self.defaults)

    def save_setting(self, key, value):
        self.settings[key] = value
        try:
            data = json.dumps(self.settings, indent=4).encode('utf-8')
            with open(self.config_path, 'wb') as f:
                f.write(data)
            
            # Write SHA-256 signature
            with open(self.sig_path, 'w', encoding='utf-8') as sf:
                sf.write(self._calculate_checksum(data))
        except Exception as e:
            logger.error("Failed to save config: %s", e, exc_info=True)


config = ConfigManager()