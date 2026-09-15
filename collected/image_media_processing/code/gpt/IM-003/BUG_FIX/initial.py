from pathlib import Path
from PIL import Image


def convert_format(input_dir, output_dir, target_format):
    """
    Convert all PNG/JPEG images in input_dir to PNG or JPEG.

    Returns:
        dict: {
            'processed_count': int,
            'skipped': list[str]
        }
    """
    target_format = target_format.upper()

    if target_format not in {"PNG", "JPEG"}:
        raise ValueError("target_format must be 'PNG' or 'JPEG'")

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg"}
    processed_count = 0
    skipped = []

    for input_path in input_dir.rglob("*"):
        if not input_path.is_file():
            continue

        if input_path.suffix.lower() not in valid_extensions:
            skipped.append(str(input_path))
            continue

        try:
            with Image.open(input_path) as img:
                # JPEG doesn't support transparency.
                if target_format == "JPEG":
                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        rgba = img.convert("RGBA")
                        background = Image.new("RGB", rgba.size, "white")
                        background.paste(rgba, mask=rgba.getchannel("A"))
                        img = background
                    else:
                        img = img.convert("RGB")

                elif target_format == "PNG":
                    # PNG supports RGB/RGBA and other modes.
                    if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                        img = img.convert("RGBA")

                # Preserve the directory structure.
                relative_path = input_path.relative_to(input_dir)
                output_path = output_dir / relative_path.with_suffix(
                    ".png" if target_format == "PNG" else ".jpg"
                )

                output_path.parent.mkdir(parents=True, exist_ok=True)

                img.save(output_path, format=target_format)
                processed_count += 1

        except (OSError, ValueError) as exc:
            skipped.append(f"{input_path}: {exc}")

    return {
        "processed_count": processed_count,
        "skipped": skipped,
    }