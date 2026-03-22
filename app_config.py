import json
import os


class ConfigManager:
    def __init__(self):
        self.config_path = "config.json"
        self.defaults = {
            "theme": "Dark OLED",
            "history_limit": "100 Records",
            "startup": True,
            "hotkey": "alt"
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return {**self.defaults, **json.load(f)}
        return self.defaults

    def save_setting(self, key, value):
        self.settings[key] = value
        with open(self.config_path, 'w') as f:
            json.dump(self.settings, f, indent=4)


config = ConfigManager()
