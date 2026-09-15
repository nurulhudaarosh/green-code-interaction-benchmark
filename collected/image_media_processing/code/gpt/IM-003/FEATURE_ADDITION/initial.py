from pathlib import Path
from PIL import Image


def convert_format(input_dir, output_dir, target_format):
    """
    Convert all images in input_dir to PNG or JPEG.

    Args:
        input_dir: Directory containing input images.
        output_dir: Directory where converted images are saved.
        target_format: "PNG" or "JPEG".

    Returns:
        Number of successfully converted images.
    """
    target_format = target_format.upper()

    if target_format not in {"PNG", "JPEG"}:
        raise ValueError("target_format must be 'PNG' or 'JPEG'")

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    supported_extensions = {
        ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"
    }

    converted_count = 0

    for file_path in input_path.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() not in supported_extensions:
            continue

        try:
            with Image.open(file_path) as img:
                if target_format == "JPEG":
                    # Safely flatten transparency onto a white background.
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        img = img.convert("RGBA")
                        background = Image.new("RGB", img.size, "white")
                        background.paste(img, mask=img.getchannel("A"))
                        img = background
                    else:
                        img = img.convert("RGB")

                    output_file = output_path / f"{file_path.stem}.jpg"
                    img.save(output_file, "JPEG", quality=95)

                else:  # PNG
                    # PNG supports transparency, so preserve it where possible.
                    if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                        img = img.convert("RGBA")

                    output_file = output_path / f"{file_path.stem}.png"
                    img.save(output_file, "PNG")

                converted_count += 1

        except (OSError, ValueError):
            # Skip files that Pillow cannot decode/convert.
            continue

    return converted_count