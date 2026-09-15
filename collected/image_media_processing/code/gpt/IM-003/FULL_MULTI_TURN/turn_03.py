from pathlib import Path
from PIL import Image


def convert_format(
    input_dir,
    output_dir,
    target_format,
    background_color=(255, 255, 255),
):
    """
    Convert all PNG/JPEG images in input_dir to PNG or JPEG.

    For JPEG output, transparent images are composited onto
    background_color before saving.

    Args:
        input_dir: Directory containing input images.
        output_dir: Directory where converted images are saved.
        target_format: "PNG" or "JPEG".
        background_color: RGB tuple used for flattening transparency
                          when converting to JPEG. Defaults to white.

    Returns:
        int: Number of successfully converted images.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

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
            "background_color must be an RGB tuple with values from 0 to 255"
        )

    extensions = {".png", ".jpg", ".jpeg"}
    converted = 0

    for path in input_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue

        try:
            with Image.open(path) as img:
                if target_format == "JPEG":
                    # Flatten transparency onto the requested background.
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        img = img.convert("RGBA")

                        background = Image.new(
                            "RGB",
                            img.size,
                            background_color,
                        )
                        background.paste(
                            img,
                            mask=img.getchannel("A"),
                        )
                        img = background
                    else:
                        img = img.convert("RGB")

                    output_path = output_dir / f"{path.stem}.jpg"
                    img.save(output_path, format="JPEG")

                else:
                    output_path = output_dir / f"{path.stem}.png"
                    img.save(output_path, format="PNG")

                converted += 1

        except (OSError, ValueError):
            continue

    return converted