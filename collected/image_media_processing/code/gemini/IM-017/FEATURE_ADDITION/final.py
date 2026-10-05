from PIL import Image
from PIL.PngImagePlugin import PngInfo


def embed_tags(
    input_path: str,
    output_path: str,
    tags: dict[str, str],
    compress_level: int | None = None,
) -> None:
    """
    Embed custom key-value string metadata into a PNG file's text chunks.

    :param input_path: Path to the input PNG image.
    :param output_path: Path to write the output PNG image.
    :param tags: Dictionary of string key-value pairs to embed.
    :param compress_level: Optional compression level (0-9).
                           0 = no compression (fastest), 9 = max compression (smallest file size).
    """
    if compress_level is not None and not (0 <= compress_level <= 9):
        raise ValueError("compress_level must be an integer between 0 and 9.")

    with Image.open(input_path) as img:
        png_info = PngInfo()

        # Preserve existing text metadata if present
        if hasattr(img, "info"):
            for key, val in img.info.items():
                if isinstance(val, str):
                    png_info.add_text(key, val)

        # Add or overwrite with new key-value pairs
        for key, value in tags.items():
            png_info.add_text(str(key), str(value))

        # Build save arguments
        save_kwargs = {"pnginfo": png_info}
        if compress_level is not None:
            save_kwargs["compress_level"] = compress_level

        # Save image with embedded PNG metadata chunks and optional compression level
        img.save(output_path, format="PNG", **save_kwargs)


def read_tags(image_path: str) -> dict[str, str]:
    """Read custom string key-value metadata from a PNG file."""
    with Image.open(image_path) as img:
        return {
            key: value
            for key, value in img.info.items()
            if isinstance(value, str)
        }