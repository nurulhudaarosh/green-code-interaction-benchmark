from PIL import Image, PngImagePlugin


def embed_tags(input_path, output_path, tags):
    """
    Embed custom string key/value metadata into PNG text chunks.

    Parameters:
        input_path: Path to the input PNG.
        output_path: Path where the output PNG will be saved.
        tags: Dictionary containing string keys and string values.
    """
    if not isinstance(tags, dict):
        raise TypeError("tags must be a dictionary")

    pnginfo = PngImagePlugin.PngInfo()

    for key, value in tags.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("Metadata keys and values must be strings")
        pnginfo.add_text(key, value)

    with Image.open(input_path) as img:
        img.save(output_path, format="PNG", pnginfo=pnginfo)


def read_tags(image_path):
    """
    Read custom string key/value metadata from PNG text chunks.

    Returns:
        dict: Metadata key/value pairs.
    """
    with Image.open(image_path) as img:
        # Pillow exposes PNG text chunks through img.text.
        return dict(img.text)