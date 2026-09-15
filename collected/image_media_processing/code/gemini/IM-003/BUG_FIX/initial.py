import os
from PIL import Image

def convert_format(input_dir: str, output_dir: str, target_format: str) -> None:
    """
    Converts all images in input_dir to either 'PNG' or 'JPEG' format and saves them in output_dir.
    Handles transparent backgrounds (RGBA/P modes) safely by flattening them onto a white background for JPEG output.
    """
    target_format = target_format.upper()
    if target_format in ["JPG", "JPEG"]:
        target_format = "JPEG"
        ext = ".jpg"
    elif target_format == "PNG":
        target_format = "PNG"
        ext = ".png"
    else:
        raise ValueError("target_format must be either 'PNG' or 'JPEG'")

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        # Skip directories
        if not os.path.isfile(input_path):
            continue

        try:
            with Image.open(input_path) as img:
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(output_dir, f"{base_name}{ext}")

                # Handle transparency flattening for JPEG format
                if target_format == "JPEG":
                    # Convert indexed/palette images with transparency to RGBA first
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        img = img.convert("RGBA")
                        # Create a solid white background image
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        # Paste using alpha channel as mask
                        background.paste(img, mask=img.split()[3])
                        img = background
                    elif img.mode != "RGB":
                        img = img.convert("RGB")
                
                img.save(output_path, format=target_format)
                print(f"Converted: {filename} -> {os.path.basename(output_path)}")

        except (IOError, SyntaxError):
            # Ignore non-image files or corrupted images
            continue