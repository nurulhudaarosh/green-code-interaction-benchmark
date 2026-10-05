from pathlib import Path
from PIL import Image


def bulk_reencode(input_dir, output_dir, quality):
    """
    Re-encode every valid image in input_dir as JPEG.

    Returns a list containing the original size, re-encoded size,
    and compression ratio for each image.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not 1 <= quality <= 95:
        raise ValueError("quality must be between 1 and 95")

    results = []

    for path in input_dir.iterdir():
        if not path.is_file():
            continue

        try:
            original_size = path.stat().st_size

            with Image.open(path) as img:
                # Always convert to RGB before saving as JPEG.
                img = img.convert("RGB")

                output_path = output_dir / f"{path.stem}.jpg"
                img.save(output_path, format="JPEG", quality=quality)

            reencoded_size = output_path.stat().st_size

            compression_ratio = (
                original_size / reencoded_size
                if reencoded_size > 0
                else float("inf")
            )

            result = {
                "filename": path.name,
                "original_size": original_size,
                "reencoded_size": reencoded_size,
                "compression_ratio": compression_ratio,
            }

            results.append(result)

            print(
                f"{path.name}: "
                f"{original_size} -> {reencoded_size} bytes, "
                f"compression ratio = {compression_ratio:.2f}:1"
            )

        except (OSError, ValueError) as e:
            print(f"Skipping {path.name}: {e}")

    return results