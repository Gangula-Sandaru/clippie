import keyboard
from app_config import config
from utils.logger import logger

# Permitted hotkey triggers to prevent arbitrary string injection
ALLOWED_HOTKEYS = {
    "alt", "ctrl", "shift", "windows", "win", "caps lock",
    "space", "tab", "esc", "f1", "f2", "f3", "f4", "f5",
    "f6", "f7", "f8", "f9", "f10", "f11", "f12"
}


def is_activation_key_pressed():
    """
    Checks if the user-defined hotkey from settings is held down.
    This acts as a 'safety lock' for the floating window.
    """
    saved_hotkey = config.settings.get("hotkey", "alt").strip().lower()

    if saved_hotkey not in ALLOWED_HOTKEYS:
        logger.warning("Disallowed or invalid hotkey attempted: '%s'. Falling back to 'alt'.", saved_hotkey)
        saved_hotkey = "alt"

    try:
        return keyboard.is_pressed(saved_hotkey)
    except Exception as e:
        logger.error("Error checking hotkey '%s': %s", saved_hotkey, e)
        return False