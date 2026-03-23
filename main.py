import os
import sys
import threading
from PyQt5.QtWidgets import QApplication

from app_config import config
from themes.theme_manager import theme_engine

from ui.main_window import MainWindow
from ui.starting_round_window import FloatingButton
from db.database import create_table
from clipboard.monitor import ClipboardMonitor


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



if __name__ == "__main__":
    # Initialize Database
    create_table()

    # --- SETTINGS INITIALIZATION ---
    # Load the theme saved in config.json and apply it to the engine
    saved_theme = config.settings.get("theme", "Dark OLED")
    theme_engine.set_theme(saved_theme)

    # Note: ClipboardMonitor already imports 'config', so it will
    # use the 'history_limit' and 'startup' settings automatically.
    # --- --- --- --- --- --- --- ---

    # Start Clipboard Monitor Thread
    monitor = ClipboardMonitor()
    t = threading.Thread(target=monitor.run, daemon=True)
    t.start()

    app = QApplication(sys.argv)

    # Initialize Main Window (Styles will now be applied from the start)
    main_win = MainWindow()

    # Initialize and show the Floating Button
    floater = FloatingButton(main_win)
    floater.show()

    if config.settings.get("first_run", True):
        from ui.onboarding_window import OnboardingWindow
        onboarding = OnboardingWindow()
        onboarding.exec_()

    sys.exit(app.exec_())