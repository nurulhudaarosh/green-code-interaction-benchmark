id="r7k42"
from pathlib import Path
from PIL import Image


def bulk_reencode(input_dir, output_dir, quality):
    """
    Re-encode every valid image in input_dir as JPEG.

    Returns:
        dict containing per-file results plus:
        "__summary__": {
            "total_original_bytes": int,
            "total_reencoded_bytes": int,
            "overall_ratio": float
        }
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    total_original_bytes = 0
    total_reencoded_bytes = 0

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

            # Update overall totals only for successfully processed files.
            total_original_bytes += original_bytes
            total_reencoded_bytes += reencoded_bytes

        except (OSError, ValueError):
            # Skip files that cannot be processed as images.
            continue

    # Calculate overall compression ratio from the totals.
    overall_ratio = (
        total_original_bytes / total_reencoded_bytes
        if total_reencoded_bytes > 0
        else float("inf")
    )

    results["__summary__"] = {
        "total_original_bytes": total_original_bytes,
        "total_reencoded_bytes": total_reencoded_bytes,
        "overall_ratio": overall_ratio,
    }

    return results