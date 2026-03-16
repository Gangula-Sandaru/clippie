import pyperclip
import time
from db.database import add_item


class ClipboardMonitor:
    def __init__(self):
        self.last_clipboard = ""

    def run(self):
        print("Clipboard monitor started...")
        while True:
            text = pyperclip.paste()
            if text and text != self.last_clipboard:
                print(f"New clipboard item: {text}")
                add_item(text)
                self.last_clipboard = text
            time.sleep(0.5)
