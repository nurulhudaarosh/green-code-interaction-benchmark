import os
from pathlib import Path
from PIL import Image
import sys


def bulk_reencode(input_dir, output_dir, quality=85):
    """
    Re-encode every image in input_dir as JPEG at the given quality.
    
    Args:
        input_dir (str): Source directory containing images.
        output_dir (str): Destination directory for re-encoded JPEGs.
        quality (int): JPEG quality (1-100). Default 85.
    
    Returns:
        dict: Summary with totals and per-file details.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extensions Pillow can typically open
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif",
                  ".tif", ".tiff", ".webp", ".ppm", ".pgm"}

    results = []
    total_original = 0
    total_reencoded = 0

    for src_path in sorted(input_dir.rglob("*")):
        if not src_path.is_file():
            continue
        if src_path.suffix.lower() not in image_exts:
            continue

        rel_path = src_path.relative_to(input_dir)
        dst_path = (output_dir / rel_path).with_suffix(".jpg")
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        original_size = src_path.stat().st_size

        try:
            with Image.open(src_path) as img:
                # Convert to RGB (JPEG doesn't support alpha/palette modes)
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                img.save(dst_path, "JPEG", quality=quality, optimize=True)

        except Exception as e:
            print(f"  [SKIP] {rel_path}: {e}", file=sys.stderr)
            continue

        reencoded_size = dst_path.stat().st_size
        ratio = original_size / reencoded_size if reencoded_size else 0

        total_original += original_size
        total_reencoded += reencoded_size

        results.append({
            "file": str(rel_path),
            "original_bytes": original_size,
            "reencoded_bytes": reencoded_size,
            "ratio": ratio,
        })

        print(f"{str(rel_path):<50} "
              f"{_human(original_size):>10} -> {_human(reencoded_size):>10}  "
              f"({ratio:.2f}x)")

    # Summary
    overall_ratio = total_original / total_reencoded if total_reencoded else 0
    print("\n" + "=" * 80)
    print(f"Files processed:    {len(results)}")
    print(f"Total original:     {_human(total_original)}")
    print(f"Total re-encoded:   {_human(total_reencoded)}")
    print(f"Overall ratio:      {overall_ratio:.2f}x  "
          f"(saved {_human(total_original - total_reencoded)})")

    return {
        "files": results,
        "count": len(results),
        "total_original_bytes": total_original,
        "total_reencoded_bytes": total_reencoded,
        "overall_ratio": overall_ratio,
    }


def _human(n):
    """Format bytes as a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Bulk re-encode images to JPEG.")
    p.add_argument("input_dir")
    p.add_argument("output_dir")
    p.add_argument("-q", "--quality", type=int, default=85)
    args = p.parse_args()

    bulk_reencode(args.input_dir, args.output_dir, args.quality)