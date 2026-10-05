id="74126"
from PIL import Image, PngImagePlugin


def embed_tags(input_path, output_path, tags, compress_level=None):
    """
    Store custom string key/value metadata in PNG text chunks.

    Args:
        input_path: Path to the input PNG image.
        output_path: Path to the output PNG image.
        tags: Dictionary of string keys and values. May be empty.
        compress_level: Optional PNG compression level from 0 to 9.
    """
    if not isinstance(tags, dict):
        raise TypeError("tags must be a dictionary")

    if compress_level is not None:
        if not isinstance(compress_level, int) or isinstance(compress_level, bool):
            raise TypeError("compress_level must be an integer from 0 to 9")
        if not 0 <= compress_level <= 9:
            raise ValueError("compress_level must be between 0 and 9")

    pnginfo = PngImagePlugin.PngInfo()

    # This loop safely does nothing when tags == {}.
    for key, value in tags.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("PNG metadata keys and values must be strings")
        pnginfo.add_text(key, value)

    save_kwargs = {
        "format": "PNG",
        "pnginfo": pnginfo,
    }

    if compress_level is not None:
        save_kwargs["compress_level"] = compress_level

    with Image.open(input_path) as img:
        img.save(output_path, **save_kwargs)


def read_tags(image_path):
    """
    Retrieve all custom text metadata from a PNG image.

    Returns an empty dictionary if the image contains no text chunks.
    """
    with Image.open(image_path) as img:
        return dict(img.text)