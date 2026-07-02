import pyperclip
import time
import os
import hashlib
from PIL import ImageGrab
from db.database import add_item
from app_config import get_writable_path

from PyQt5.QtCore import QObject, pyqtSignal

last_ui_copy = None
last_ui_image_hash = None

class ClipboardMonitor(QObject):
    item_added = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.last_clipboard = ""
        self.last_image_hash = ""
        self.is_paused = False

    def run(self):
        global last_ui_copy, last_ui_image_hash
        print("Clipboard monitor started...")
        
        image_dir = get_writable_path("images")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
            
        while True:
            try:
                if getattr(self, 'is_paused', False):
                    time.sleep(0.5)
                    continue
                    
                # 1. Check for image
                img = ImageGrab.grabclipboard()
                if img is not None and hasattr(img, 'save'):
                    # Convert to RGB so we can save as PNG
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    img_byte_arr = img.tobytes()
                    img_hash = hashlib.md5(img_byte_arr).hexdigest()
                    
                    if img_hash != self.last_image_hash:
                        if img_hash == last_ui_image_hash:
                            self.last_image_hash = img_hash
                            time.sleep(0.5)
                            continue
                            
                        filename = f"img_{img_hash}.png"
                        filepath = os.path.join(image_dir, filename)
                        img.save(filepath, "PNG")
                        
                        add_item(filepath, manual_tag="Image")
                        self.item_added.emit()
                        self.last_image_hash = img_hash
                        self.last_clipboard = "" # clear text check
                    
                    time.sleep(0.5)
                    continue
                elif isinstance(img, list) and len(img) > 0:
                    # File(s) copied (path list), not image data directly
                    for file_path in img:
                        if isinstance(file_path, str) and file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.ico')):
                            if file_path != self.last_clipboard:
                                add_item(file_path, manual_tag="Image")
                                self.item_added.emit()
                                self.last_clipboard = file_path
                                self.last_image_hash = "" # clear image data check
                    time.sleep(0.5)
                    continue
                
                # 2. Check for text
                text = pyperclip.paste()
                if text and text != self.last_clipboard:
                    if text == last_ui_copy:
                        self.last_clipboard = text
                        continue
                    add_item(text)
                    self.item_added.emit()
                    self.last_clipboard = text
                    self.last_image_hash = "" # clear image check
                    
                time.sleep(0.5)
            except Exception as e:
                time.sleep(0.5)
