import winreg
import os
import sys


def set_startup(enabled=True):
    # This is YOUR app's identifier (You can change this to 'Clippie')
    app_name = "Clippie"

    # This is the ADDRESS (Never change this)
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        # We open the 'ADDRESS'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

        if enabled:
            if getattr(sys, 'frozen', False):
                app_path = f'"{os.path.realpath(sys.executable)}" --autostart'
            else:
                app_path = f'"{os.path.realpath(sys.executable)}" "{os.path.realpath(sys.argv[0])}" --autostart'
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        else:
            # We remove 'Clippie' from that address
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Error: {e}")