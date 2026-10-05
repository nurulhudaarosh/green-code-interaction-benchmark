from pathlib import Path
from PIL import Image


def bulk_reencode(input_dir, output_dir, quality):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for path in input_dir.iterdir():
        if not path.is_file():
            continue

        try:
            with Image.open(path) as img:
                # Convert to RGB so RGBA/P images can be saved as JPEG.
                img = img.convert("RGB")

                output_path = output_dir / f"{path.stem}.jpg"
                img.save(output_path, "JPEG", quality=quality)

            original_bytes = path.stat().st_size
            reencoded_bytes = output_path.stat().st_size

            ratio = (
                original_bytes / reencoded_bytes
                if reencoded_bytes > 0
                else float("inf")
            )

            results[path.name] = {
                "original_bytes": original_bytes,
                "reencoded_bytes": reencoded_bytes,
                "compression_ratio": ratio,
            }

        except (OSError, ValueError):
            # Skip files that PIL cannot open as images.
            continue

    return results