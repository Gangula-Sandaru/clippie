from PIL import ImageGrab

def capture_screen_rect(x, y, width, height):
    """
    Captures a specific rectangle from the screen.
    Returns a PIL Image object.
    """
    # ImageGrab.grab takes a bbox: (left, top, right, bottom)
    bbox = (x, y, x + width, y + height)
    return ImageGrab.grab(bbox=bbox)
