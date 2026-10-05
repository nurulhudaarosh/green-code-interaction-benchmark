from PIL import Image


def read_tags(image_path: str) -> dict[str, str]:
    """Return all PNG text-chunk key/value pairs (tEXt, zTXt, iTXt)."""
    with Image.open(image_path) as img:
        if img.format != "PNG":
            raise ValueError("Not a PNG file")
        img.load()  # text chunks after IDAT are only parsed once the image is loaded
        return {str(k): str(v) for k, v in img.text.items()}