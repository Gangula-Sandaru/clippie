import os
import pytesseract
import pyperclip
from db.database import add_item

def process_image(image):
    """
    Takes a PIL Image, processes it via Tesseract OCR,
    copies the resulting text to the clipboard, and adds to history.
    """
    # Auto-configure tesseract path for Windows users if not in system PATH
    if os.name == 'nt':
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.getenv('LOCALAPPDATA', ''), r"Tesseract-OCR\tesseract.exe")
        ]
        for p in common_paths:
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                break

    text = pytesseract.image_to_string(image)
    text = text.strip()
    
    if text:
        from app_config import config
        if config.settings.get("ocr_auto_copy", True):
            pyperclip.copy(text)
            
        add_item(text, manual_tag="OCR")
        return text
    else:
        return ""
