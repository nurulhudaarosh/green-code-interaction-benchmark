from pathlib import Path
from PIL import Image


def bulk_reencode(input_dir, output_dir, quality):
    """
    Re-encode every valid image in input_dir as JPEG.

    Returns:
        dict: {
            filename: {
                "original_bytes": int,
                "reencoded_bytes": int,
                "ratio": float
            }
        }
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for path in input_dir.iterdir():
        if not path.is_file():
            continue

        try:
            original_bytes = path.stat().st_size

            with Image.open(path) as img:
                # Convert all image modes, including P and RGBA,
                # to RGB before saving as JPEG.
                img = img.convert("RGB")

                output_path = output_dir / f"{path.stem}.jpg"
                img.save(output_path, format="JPEG", quality=quality)

            reencoded_bytes = output_path.stat().st_size

            ratio = (
                original_bytes / reencoded_bytes
                if reencoded_bytes > 0
                else float("inf")
            )

            results[path.name] = {
                "original_bytes": original_bytes,
                "reencoded_bytes": reencoded_bytes,
                "ratio": ratio,
            }

        except (OSError, ValueError):
            # Skip files that cannot be opened or processed as images.
            continue

    return results