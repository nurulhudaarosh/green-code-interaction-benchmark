import os
from pathlib import Path
from PIL import Image

# Common image extensions to attempt re-encoding
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}


def bulk_reencode(input_dir, output_dir, quality):
    """
    Re-encode every image in input_dir as JPEG at the given quality,
    writing results to output_dir.

    Args:
        input_dir (str | Path): Directory containing source images.
        output_dir (str | Path): Directory to write re-encoded JPEGs.
        quality (int): JPEG quality (1-95 recommended; 100 disables compression).

    Returns:
        list[dict]: One record per successfully re-encoded file with keys:
                    'file', 'original_bytes', 'reencoded_bytes', 'ratio'.
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

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python bulk_reencode.py <input_dir> <output_dir> <quality>")
        sys.exit(1)

    bulk_reencode(sys.argv[1], sys.argv[2], int(sys.argv[3]))