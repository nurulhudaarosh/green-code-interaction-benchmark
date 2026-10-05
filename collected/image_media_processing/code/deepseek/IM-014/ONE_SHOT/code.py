import os
from pathlib import Path
from PIL import Image

# Common image extensions to look for
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}


def bulk_reencode(input_dir, output_dir, quality):
    """
    Re-encode every image in input_dir as JPEG at the given quality.

    Args:
        input_dir (str): Directory containing source images.
        output_dir (str): Directory to write re-encoded JPEGs into.
        quality (int): JPEG quality (1-100).

    Returns:
        list[dict]: Per-file report with original/reencoded sizes and ratio.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    if not (1 <= quality <= 100):
        raise ValueError("quality must be between 1 and 100")

    output_dir.mkdir(parents=True, exist_ok=True)

    report = []

    for src_path in sorted(input_dir.rglob("*")):
        if not src_path.is_file():
            continue
        if src_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        # Preserve relative subdirectory structure, force .jpg extension
        rel = src_path.relative_to(input_dir)
        dst_path = (output_dir / rel).with_suffix(".jpg")
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        original_size = src_path.stat().st_size

        try:
            with Image.open(src_path) as img:
                # Convert to RGB (JPEG doesn't support alpha/palette modes)
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                img.save(dst_path, "JPEG", quality=quality, optimize=True)

            reencoded_size = dst_path.stat().st_size
            ratio = original_size / reencoded_size if reencoded_size else float("inf")

            entry = {
                "file": str(rel),
                "original_size": original_size,
                "reencoded_size": reencoded_size,
                "ratio": ratio,
                "status": "ok",
            }
        except Exception as e:
            entry = {
                "file": str(rel),
                "original_size": original_size,
                "reencoded_size": None,
                "ratio": None,
                "status": f"error: {e}",
            }

        report.append(entry)

        # Print per-file report
        if entry["status"] == "ok":
            print(
                f"{entry['file']}: "
                f"{_fmt(entry['original_size'])} -> {_fmt(entry['reencoded_size'])} "
                f"(ratio {entry['ratio']:.2f}x)"
            )
        else:
            print(f"{entry['file']}: {entry['status']}")

    # Summary
    total_original = sum(e["original_size"] for e in report if e["status"] == "ok")
    total_reencoded = sum(e["reencoded_size"] for e in report if e["status"] == "ok")
    overall_ratio = total_original / total_reencoded if total_reencoded else 0

    print("\n--- Summary ---")
    print(f"Files processed: {len([e for e in report if e['status'] == 'ok'])}")
    print(f"Total original:  {_fmt(total_original)}")
    print(f"Total reencoded: {_fmt(total_reencoded)}")
    print(f"Overall ratio:   {overall_ratio:.2f}x")

    return report


def _fmt(num_bytes):
    """Format a byte count as a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python bulk_reencode.py <input_dir> <output_dir> <quality>")
        sys.exit(1)

    bulk_reencode(sys.argv[1], sys.argv[2], int(sys.argv[3]))