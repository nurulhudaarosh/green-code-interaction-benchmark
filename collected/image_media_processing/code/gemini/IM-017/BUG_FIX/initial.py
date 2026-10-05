from PIL import Image, PngImagePlugin

def embed_tags(input_path: str, output_path: str, tags: dict[str, str]) -> None:
    """
    Embeds custom key-value string metadata into a PNG image using tEXt/iTXt chunks.
    
    :param input_path: Path to the source image file.
    :param output_path: Path where the new image with embedded tags will be saved.
    :param tags: Dictionary containing string key-value pairs to embed.
    """
    with Image.open(input_path) as img:
        # PngInfo object holds the PNG metadata chunks
        png_info = PngImagePlugin.PngInfo()

        # Preserve existing PNG text metadata if present
        for key, value in img.info.items():
            if isinstance(value, str):
                png_info.add_text(key, value)

        # Add or overwrite with new tags
        for key, value in tags.items():
            png_info.add_text(str(key), str(value))

        # Save image with the updated pnginfo metadata block
        img.save(output_path, format="PNG", pnginfo=png_info)


def read_tags(image_path: str) -> dict[str, str]:
    """
    Retrieves embedded text metadata chunks from a PNG file.
    
    :param image_path: Path to the PNG file.
    :return: Dictionary containing key-value metadata pairs.
    """
    with Image.open(image_path) as img:
        # img.info extracts non-pixel chunk data including standard text keys
        return {key: val for key, val in img.info.items() if isinstance(val, str)}