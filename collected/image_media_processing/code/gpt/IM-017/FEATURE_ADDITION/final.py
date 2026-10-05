from PIL import Image, PngImagePlugin


def embed_tags(input_path, output_path, tags, compress_level=None):
    """
    Embed custom string key/value metadata into PNG text chunks.

    Parameters:
        input_path: Path to the input PNG.
        output_path: Path where the output PNG will be saved.
        tags: Dictionary containing string keys and string values.
        compress_level: Optional PNG compression level from 0 to 9.
    """
    if not isinstance(tags, dict):
        raise TypeError("tags must be a dictionary")

    if compress_level is not None:
        if not isinstance(compress_level, int) or not 0 <= compress_level <= 9:
            raise ValueError("compress_level must be an integer from 0 to 9")

    pnginfo = PngImagePlugin.PngInfo()

    for key, value in tags.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("Metadata keys and values must be strings")
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
    Read custom string key/value metadata from PNG text chunks.

    Returns:
        dict: Metadata key/value pairs.
    """
    with Image.open(image_path) as img:
        return dict(img.text)