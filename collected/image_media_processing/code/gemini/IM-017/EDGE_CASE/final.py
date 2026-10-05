from PIL import Image
from PIL.PngImagePlugin import PngInfo

# Built-in Pillow/PNG metadata keys to ignore when returning custom tags
PILLOW_INTERNAL_KEYS = {
    'dpi', 'aspect', 'gamma', 'interlace', 'transparency', 
    'chromaticity', 'srgb', 'exif', 'icc_profile', 'photoshop'
}

def embed_tags(input_path: str, output_path: str, tags: dict[str, str]) -> None:
    """
    Embeds key/value string metadata into a PNG image using tEXt chunks.
    Passing an empty dictionary ({}) retains the image without adding new tags.
    """
    with Image.open(input_path) as img:
        meta = PngInfo()
        
        # Add provided tags as tEXt/iTXt chunks
        for key, value in tags.items():
            meta.add_text(str(key), str(value))
        
        # Save image with pnginfo container (works even if empty)
        img.save(output_path, "PNG", pnginfo=meta)


def read_tags(image_path: str) -> dict[str, str]:
    """
    Reads custom string metadata stored in a PNG file.
    Returns an empty dict {} if no custom tags exist or if an empty dict was embedded.
    """
    with Image.open(image_path) as img:
        # Filter out internal/header PNG keys populated automatically by Pillow
        custom_tags = {
            k: v for k, v in img.info.items() 
            if k.lower() not in PILLOW_INTERNAL_KEYS and isinstance(v, str)
        }
        return custom_tags