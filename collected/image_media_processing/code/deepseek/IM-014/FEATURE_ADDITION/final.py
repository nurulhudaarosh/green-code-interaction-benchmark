import os
from pathlib import Path
from PIL import Image

# Common image extensions to attempt re-encoding
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}

SUMMARY_KEY = "__summary__"


def bulk_reencode(input_dir, output_dir, quality):
    """
    Re-encode every image in input_dir as JPEG at the given quality,
    writing results to output_dir.

    Args:
        input_dir (str | Path): Directory containing source images.
        output_dir (str | Path): Directory to write re-encoded JPEGs.
        quality (int): JPEG quality (1-100).

    Returns:
        list[dict]: One record per successfully re-encoded file, plus a final
                    summary record under key '__summary__' with:
                      - 'file': '__summary__'
                      - 'count': number of files processed
                      - 'original_bytes': total size of originals
                      - 'reencoded_bytes': total size of outputs
                      - 'ratio': overall original_bytes / reencoded_bytes
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")
    if not (1 <= quality <= 100):
        raise ValueError("quality must be between 1 and 100")

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for src in sorted(input_dir.rglob("*")):
        if not src.is_file() or src.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        # Preserve relative directory structure, force .jpg extension
        rel = src.relative_to(input_dir).with_suffix(".jpg")
        dst = output_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(src) as img:
                # JPEG can't store alpha; composite onto white if needed
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                img.save(dst, "JPEG", quality=quality, optimize=True)

        except Exception as e:
            print(f"[SKIP] {src}: {e}")
            continue

        original_bytes = src.stat().st_size
        reencoded_bytes = dst.stat().st_size
        ratio = original_bytes / reencoded_bytes if reencoded_bytes else float("inf")

        record = {
            "file": str(src),
            "original_bytes": original_bytes,
            "reencoded_bytes": reencoded_bytes,
            "ratio": ratio,
        }
        results.append(record)

        print(
            f"{src} -> {dst}\n"
            f"  original:   {original_bytes:>10,} bytes\n"
            f"  reencoded:  {reencoded_bytes:>10,} bytes\n"
            f"  ratio:      {ratio:>10.2f}x"
        )

    # --- Build summary -----------------------------------------------------
    total_in = sum(r["original_bytes"] for r in results)
    total_out = sum(r["reencoded_bytes"] for r in results)
    overall_ratio = total_in / total_out if total_out else float("inf")

    summary = {
        "file": SUMMARY_KEY,
        "count": len(results),
        "original_bytes": total_in,
        "reencoded_bytes": total_out,
        "ratio": overall_ratio,
    }
    results.append(summary)

    print(
        f"\n=== Summary ===\n"
        f"  files processed: {len(results) - 1}\n"
        f"  original:        {total_in:>12,} bytes\n"
        f"  reencoded:       {total_out:>12,} bytes\n"
        f"  overall ratio:   {overall_ratio:>12.2f}x\n"
    )

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python bulk_reencode.py <input_dir> <output_dir> <quality>")
        sys.exit(1)

    records = bulk_reencode(sys.argv[1], sys.argv[2], int(sys.argv[3]))

    # Example: pull just the summary
    summary = next(r for r in records if r["file"] == SUMMARY_KEY)
    print("Summary dict:", summary)