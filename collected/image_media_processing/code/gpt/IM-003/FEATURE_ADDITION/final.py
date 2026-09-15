from pathlib import Path
from PIL import Image


def convert_format(input_dir, output_dir, target_format,
                   background_color=(255, 255, 255)):
    """
    Convert all images in input_dir to PNG or JPEG.

    Args:
        input_dir: Directory containing input images.
        output_dir: Directory where converted images are saved.
        target_format: "PNG" or "JPEG".
        background_color: RGB tuple used to flatten transparency
                          when converting to JPEG. Defaults to white.

    Returns:
        Number of successfully converted images.
    """
    target_format = target_format.upper()

    if target_format not in {"PNG", "JPEG"}:
        raise ValueError("target_format must be 'PNG' or 'JPEG'")

    if (
        not isinstance(background_color, tuple)
        or len(background_color) != 3
        or not all(isinstance(c, int) and 0 <= c <= 255
                   for c in background_color)
    ):
        raise ValueError(
            "background_color must be an RGB tuple of three integers "
            "between 0 and 255"
        )

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    supported_extensions = {
        ".png", ".jpg", ".jpeg", ".bmp",
        ".gif", ".tiff", ".webp"
    }

    converted_count = 0

    for file_path in input_path.iterdir():
        if (
            not file_path.is_file()
            or file_path.suffix.lower() not in supported_extensions
        ):
            continue

        try:
            with Image.open(file_path) as img:
                if target_format == "JPEG":
                    # Flatten transparency onto the requested background.
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        img = img.convert("RGBA")

                        background = Image.new(
                            "RGB",
                            img.size,
                            background_color
                        )

                        background.paste(
                            img,
                            mask=img.getchannel("A")
                        )
                        img = background
                    else:
                        img = img.convert("RGB")

                    output_file = output_path / f"{file_path.stem}.jpg"
                    img.save(output_file, "JPEG", quality=95)

                else:  # PNG
                    if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                        img = img.convert("RGBA")

                    output_file = output_path / f"{file_path.stem}.png"
                    img.save(output_file, "PNG")

                converted_count += 1

        except (OSError, ValueError):
            continue

    return converted_count