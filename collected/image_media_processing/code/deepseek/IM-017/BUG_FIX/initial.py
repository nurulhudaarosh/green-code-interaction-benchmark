from PIL import Image
from PIL.PngImagePlugin import PngInfo


def embed_tags(input_path, output_path, tags):
    """
    Embed custom key/value string metadata into a PNG file.

    Args:
        input_path:  Source PNG path.
        output_path: Destination PNG path (can equal input_path).
        tags:        Dict[str, str] of key/value pairs.
    """
    if not isinstance(tags, dict):
        raise TypeError("tags must be a dict of {str: str}")

    img = Image.open(input_path)
    if img.format != "PNG":
        raise ValueError(f"Expected PNG, got {img.format}")

    # Preserve existing metadata, then add ours
    meta = PngInfo()
    for k, v in (img.info or {}).items():
        if isinstance(v, str):
            meta.add_text(k, v)

    for k, v in tags.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise TypeError("tag keys and values must be strings")
        # add_itxt gives UTF-8 support (Pillow >= 6.0)
        meta.add_itxt(k, v, zip=False)

    # Copy pixel data without losing mode (e.g. palette/RGBA)
    img.load()
    img.save(output_path, format="PNG", pnginfo=meta)


def read_tags(image_path):
    """
    Read text-chunk metadata from a PNG file.

    Returns:
        Dict[str, str] of key/value pairs (empty if none).
    """
    img = Image.open(image_path)
    if img.format != "PNG":
        raise ValueError(f"Expected PNG, got {img.format}")

    return {
        k: v for k, v in (img.info or {}).items()
        if isinstance(v, str)
    }