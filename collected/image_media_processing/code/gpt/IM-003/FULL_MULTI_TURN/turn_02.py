from pathlib import Path
from PIL import Image


def convert_format(input_dir, output_dir, target_format):
    """
    Convert all PNG/JPEG images in input_dir to PNG or JPEG.

    Transparent images are composited onto a white background when
    converting to JPEG so transparent pixels do not become black.

    Returns:
        int: Number of successfully converted images.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_format = target_format.upper()
    if target_format not in {"PNG", "JPEG"}:
        raise ValueError("target_format must be 'PNG' or 'JPEG'")

    extensions = {".png", ".jpg", ".jpeg"}
    converted = 0

    for path in input_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue

        try:
            with Image.open(path) as img:
                if target_format == "JPEG":
                    # Composite transparency onto a white background.
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        img = img.convert("RGBA")

                        background = Image.new(
                            "RGB",
                            img.size,
                            (255, 255, 255)
                        )
                        background.paste(
                            img,
                            mask=img.getchannel("A")
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