from PIL import Image

def read_tags(image_path):
    """Return {keyword: value} for all PNG text chunks."""
    with Image.open(image_path) as img:
        # img.text is the correct, complete mapping of text chunks.
        # It works for PNG (tEXt/iTXt/zTXt) and is populated on open().
        return dict(img.text)