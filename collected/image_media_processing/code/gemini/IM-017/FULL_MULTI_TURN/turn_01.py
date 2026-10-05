from PIL import Image
from PIL.PngImagePlugin import PngInfo

def embed_tags(input_path: str, output_path: str, tags: dict[str, str]) -> None:
    """
    Embeds custom key/value string metadata into a PNG file.
    
    :param input_path: Path to the source image.
    :param output_path: Path to save the new image with embedded metadata.
    :param tags: Dictionary containing string key-value pairs to embed.
    """
    with Image.open(input_path) as img:
        # Preserve any existing metadata chunks while adding new ones
        meta = PngInfo()
        
        # Copy existing info into the new metadata object
        for key, value in img.info.items():
            if isinstance(value, str):
                meta.add_text(key, value)
                
        # Add or overwrite with new key/value tags
        for key, value in tags.items():
            meta.add_text(str(key), str(value))
            
        # Save image with updated PngInfo structure
        img.save(output_path, "PNG", pnginfo=meta)


def read_tags(image_path: str) -> dict[str, str]:
    """
    Reads text metadata chunks from a PNG file.
    
    :param image_path: Path to the PNG image.
    :return: Dictionary containing key/value metadata strings.
    """
    with Image.open(image_path) as img:
        # Filter img.info to ensure only string key/value pairs are returned
        return {
            str(k): str(v) 
            for k, v in img.info.items() 
            if isinstance(v, str)
        }