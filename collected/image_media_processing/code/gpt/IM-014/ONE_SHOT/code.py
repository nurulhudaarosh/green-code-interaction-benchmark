from pathlib import Path
from PIL import Image


def bulk_reencode(input_dir, output_dir, quality):
    """
    Re-encode every valid image in input_dir as JPEG.

    Returns:
        list of dictionaries containing:
        - file
        - original_size
        - reencoded_size
        - compression_ratio
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for src_path in input_dir.iterdir():
        if not src_path.is_file():
            continue

        try:
            with Image.open(src_path) as img:
                # JPEG does not support transparency.
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                dst_path = output_dir / f"{src_path.stem}.jpg"

                original_size = src_path.stat().st_size

                img.save(
                    dst_path,
                    format="JPEG",
                    quality=quality
                )

                reencoded_size = dst_path.stat().st_size

                compression_ratio = (
                    original_size / reencoded_size
                    if reencoded_size > 0 else float("inf")
                )

                results.append({
                    "file": src_path.name,
                    "original_size": original_size,
                    "reencoded_size": reencoded_size,
                    "compression_ratio": compression_ratio
                })

        except (OSError, ValueError):
            # Skip files that PIL cannot decode as images.
            continue

    return results