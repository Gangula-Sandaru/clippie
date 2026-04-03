import os
import pyperclip
from db.database import add_item

def translate_text(text, target_lang="auto", auto_copy=True):
    """
    Translates text to the target language.
    Since we don't have a specific translation library installed yet, 
    we'll use a placeholder logic that would normally call a translation API.
    """
    import urllib.request
    import urllib.parse
    import json
    
    if not text:
        return ""
    
    translated = text
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={encoded_text}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                translated = "".join([segment[0] for segment in data[0] if segment[0]])
    except Exception as e:
        print("Translation API Error:", e)
        translated = f"[{target_lang.upper()}] {text}"
    
    if translated:
        from app_config import config
        # Respect both the global setting and the override
        if auto_copy and config.settings.get("ocr_auto_copy", True):
            pyperclip.copy(translated)
            
        add_item(translated, manual_tag="Translate")
        return translated
    else:
        return ""

def process_translate_detailed(image, target_lang="auto", auto_copy=True):
    """
    Reuses OCR logic to get text, then translates it.
    Returns (translated_text, words) where words contain original positions.
    """
    from ocr.processing import process_image_detailed
    # Get raw text and positions first
    raw_text, words = process_image_detailed(image)
    
    if not raw_text:
        return "", []
        
    translated_text = translate_text(raw_text, target_lang=target_lang, auto_copy=auto_copy)
    
    # Translate ALL words natively via one fast HTTP batch!
    try:
        word_texts = [w['text'] for w in words]
        # Google Translate preserves \n structure safely for batches
        batch_text = "\n".join(word_texts)
        translated_batch = translate_text(batch_text, target_lang=target_lang, auto_copy=False)
        translated_list = translated_batch.split('\n')
        
        for i, w in enumerate(words):
            if i < len(translated_list) and translated_list[i].strip():
                w['translated'] = translated_list[i].strip()
            else:
                w['translated'] = w['text']
    except Exception as e:
        print("Batch translation error:", e)
        for w in words: w['translated'] = w['text']
        
    return translated_text, words
