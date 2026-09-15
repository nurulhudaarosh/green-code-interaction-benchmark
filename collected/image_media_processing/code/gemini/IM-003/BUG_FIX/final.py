import os
from PIL import Image

def convert_format(input_dir: str, output_dir: str, target_format: str) -> None:
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

        if not os.path.isfile(input_path):
            continue

        try:
            with Image.open(input_path) as img:
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(output_dir, f"{base_name}{ext}")

                if target_format == "JPEG":
                    # Convert palette images to RGBA to preserve transparency channels correctly
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")

                    # Create a white background of the exact same size
                    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    
                    # Alpha composite the image over the white background, then drop alpha channel
                    img = Image.alpha_composite(background, img).convert("RGB")

                img.save(output_path, format=target_format)
                print(f"Converted: {filename} -> {os.path.basename(output_path)}")

        except (IOError, SyntaxError):
            continue