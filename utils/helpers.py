import keyboard
from app_config import config


def is_activation_key_pressed():
    """
    Checks if the user-defined hotkey from settings is held down.
    This acts as a 'safety lock' for the floating window.
    """
    # 1. Fetch the hotkey from config (defaulting to 'alt' if not set)
    # .lower() ensures compatibility even if the user types 'ALT' or 'Alt'
    saved_hotkey = config.settings.get("hotkey", "alt").lower()

    try:
        # 2. Check if that specific key is currently pressed
        return keyboard.is_pressed(saved_hotkey)
    except Exception as e:
        # Fallback if the user enters an invalid key name
        print(f"Invalid hotkey: {saved_hotkey}. Error: {e}")
        return False