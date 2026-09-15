from pathlib import Path
from PIL import Image


def convert_format(input_dir, output_dir, target_format):
    """
    Recursively convert all images in input_dir to PNG or JPEG.

    Transparent images are composited onto a white background when
    converting to JPEG, since JPEG does not support transparency.

    Args:
        input_dir (str | Path): Source directory.
        output_dir (str | Path): Destination directory.
        target_format (str): "PNG" or "JPEG".

    Returns:
        dict: Contains processed_count and skipped files.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    target_format = target_format.upper()
    if target_format not in {"PNG", "JPEG"}:
        raise ValueError("target_format must be 'PNG' or 'JPEG'")

    output_dir.mkdir(parents=True, exist_ok=True)

    supported_extensions = {
        ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"
    }

    processed_count = 0
    skipped = []

    for input_path in input_dir.rglob("*"):
        if not input_path.is_file():
            continue

        if input_path.suffix.lower() not in supported_extensions:
            skipped.append(str(input_path))
            continue

        try:
            with Image.open(input_path) as img:
                # Preserve the directory structure.
                relative_path = input_path.relative_to(input_dir)

                new_suffix = ".png" if target_format == "PNG" else ".jpg"
                output_path = output_dir / relative_path.with_suffix(new_suffix)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if target_format == "JPEG":
                    # JPEG cannot store transparency.
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        rgba = img.convert("RGBA")

                        background = Image.new(
                            "RGB",
                            rgba.size,
                            (255, 255, 255)
                        )
                        background.paste(
                            rgba,
                            mask=rgba.getchannel("A")
                        )
                        img = background
                    else:
                        img = img.convert("RGB")

                    img.save(output_path, "JPEG", quality=95)

                else:  # PNG
                    # PNG supports RGB/RGBA and other compatible modes.
                    img.save(output_path, "PNG")

                processed_count += 1

        except (OSError, ValueError) as exc:
            skipped.append(f"{input_path}: {exc}")

    return {
        "processed_count": processed_count,
        "skipped": skipped,
    }