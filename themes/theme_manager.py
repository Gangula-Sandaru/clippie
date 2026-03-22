from PyQt5.QtCore import QObject, pyqtSignal
from themes.themes import ThemePalette


class ThemeManager(QObject):
    theme_changed = pyqtSignal(dict)  # Broadcasts the new palette

    def __init__(self):
        super().__init__()
        self.themes = {
            "Dark OLED": ThemePalette.DARK_OLED,
            "Tokyo Night": ThemePalette.TOKYO_NIGHT,
            "Light Minimal": ThemePalette.LIGHT_MINIMAL
        }
        self.current_theme_name = "Dark OLED"
        self.current_palette = self.themes[self.current_theme_name]

    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            self.current_palette = self.themes[theme_name]
            self.theme_changed.emit(self.current_palette)


# Global singleton instance
theme_engine = ThemeManager()
