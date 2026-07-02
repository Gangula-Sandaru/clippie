import json
import os
import sys


def get_writable_path(filename):
    """Redirects files to the user's AppData folder for Windows compatibility."""
    if sys.platform == "win32":
        # Points to C:\Users\Name\AppData\Roaming\Clippie
        base_path = os.path.join(os.environ.get("APPDATA"), "Clippie")
    else:
        base_path = os.path.expanduser("~/.clippie")

    if not os.path.exists(base_path):
        os.makedirs(base_path)
    return os.path.join(base_path, filename)


class ConfigManager:
    def __init__(self):
        # This is the secret sauce: use the writable path!
        self.config_path = get_writable_path("config.json")
        self.defaults = {
            "theme": "Dark OLED",
            "history_limit": "100 Records",
            "startup": True,
            "hotkey": "alt",
            "first_run": True,
            "floating_widget": True,
            "magic_ocr_animation": True,
            "ocr_auto_copy": True
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return {**self.defaults, **json.load(f)}
            except Exception:
                return self.defaults
        return self.defaults

    def save_setting(self, key, value):
        self.settings[key] = value
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")


config = ConfigManager()