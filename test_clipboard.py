import traceback
from PIL import ImageGrab
import pyperclip

print("=== Testing ImageGrab ===")
try:
    img = ImageGrab.grabclipboard()
    print("img result:", type(img))
    if img is not None:
        if hasattr(img, 'save'):
            print("It's an image object!")
            print("mode:", img.mode, "size:", img.size)
        else:
            print("It's something else! (possibly a list)", img)
except Exception as e:
    print("ImageGrab error:")
    traceback.print_exc()

print("=== Testing Pyperclip ===")
try:
    text = pyperclip.paste()
    print("text result len:", len(text))
    # print("text snippet:", repr(text[:20]))
except Exception as e:
    print("Pyperclip error:")
    traceback.print_exc()
