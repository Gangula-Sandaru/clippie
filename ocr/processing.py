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

def process_image_detailed(image):
    """
    Takes a PIL Image, processes it via Tesseract OCR to get detailed bounding boxes,
    copies the resulting full text to the clipboard, and adds to history.
    Returns (full_text, words) where words is a list of dicts with bounding box info.
    """
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

    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    except Exception as e:
        print(f"Error extracting detailed OCR: {e}")
        return "", []

    words = []
    lines = []
    current_line = []
    last_block = -1
    last_par = -1
    last_line = -1

    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if data['level'][i] == 5 and text:
            b, p, l = data['block_num'][i], data['par_num'][i], data['line_num'][i]
            # Tesseract level 5 is word
            words.append({
                'text': text,
                'left': data['left'][i],
                'top': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i],
                'conf': data['conf'][i],
                'block_num': b,
                'par_num': p,
                'line_num': l
            })
            
            if b != last_block or p != last_par or l != last_line:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                # If it's a new paragraph, we could add an extra newline, but basic joining is fine
                if (b != last_block or p != last_par) and lines:
                    lines.append("") # Adds an empty line between paragraphs
                last_block, last_par, last_line = b, p, l
            
            current_line.append(text)

    if current_line:
        lines.append(" ".join(current_line))
        
    full_text = "\n".join(lines).strip()
    
    if full_text:
        from app_config import config
        if config.settings.get("ocr_auto_copy", True):
            pyperclip.copy(full_text)
            
        add_item(full_text, manual_tag="OCR")
        return full_text, words
    else:
        return "", []
