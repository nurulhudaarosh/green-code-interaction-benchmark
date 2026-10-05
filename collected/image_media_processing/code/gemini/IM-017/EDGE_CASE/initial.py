from PIL import Image
from PIL.PngImagePlugin import PngInfo

def embed_tags(input_path: str, output_path: str, tags: dict[str, str]) -> None:
    """
    Embeds key/value string metadata into a PNG image using tEXt chunks.
    
    :param input_path: Path to the source PNG image.
    :param output_path: Path where the updated PNG image will be saved.
    :param tags: Dictionary of string keys and values to embed.
    """
    with Image.open(input_path) as img:
        # Create a PngInfo metadata container
        meta = PngInfo()
        
        # Add key-value pairs as tEXt chunks
        for key, value in tags.items():
            meta.add_text(str(key), str(value))
        
        # Save image with the custom metadata attached
        img.save(output_path, "PNG", pnginfo=meta)


def read_tags(image_path: str) -> dict[str, str]:
    """
    Reads and retrieves custom text metadata stored in a PNG file.
    
    :param image_path: Path to the PNG image.
    :return: Dictionary containing the extracted key/value metadata.
    """
    with Image.open(image_path) as img:
        # img.info contains the PNG text chunk key-value pairs
        return dict(img.info)