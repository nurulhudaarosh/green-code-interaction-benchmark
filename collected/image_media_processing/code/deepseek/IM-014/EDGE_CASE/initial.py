import os
import sys
from pathlib import Path
from PIL import Image

# Supported input formats (Pillow-readable raster images)
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff',
    '.webp', '.ppm', '.pgm', '.pbm', '.ico', '.jfif'
}


def bulk_reencode(input_dir, output_dir, quality=85):
    """
    Re-encode every image in input_dir as JPEG at the given quality,
    saving to output_dir. Reports original vs. reencoded sizes and
    per-file compression ratio.

    Args:
        input_dir (str|Path): Directory containing source images.
        output_dir (str|Path): Directory to write re-encoded JPEGs.
        quality (int): JPEG quality (1-95; 95+ is rarely worth it).

    Returns:
        dict: Summary statistics.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    if not (1 <= quality <= 100):
        raise ValueError("quality must be between 1 and 100")

    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        p for p in input_dir.rglob('*')
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print(f"No supported images found in {input_dir}")
        return {"files": 0, "total_original": 0, "total_reencoded": 0, "ratio": 1.0}

    # Column widths for aligned output
    name_w = max((len(str(f.relative_to(input_dir))) for f in files), default=20)
    name_w = min(max(name_w, 20), 80)

    header = (
        f"{'File':<{name_w}}  "
        f"{'Original':>12}  "
        f"{'Reencoded':>12}  "
        f"{'Saved':>10}  "
        f"{'Ratio':>7}"
    )
    print(header)
    print('-' * len(header))

    total_orig = 0
    total_new = 0
    ok_count = 0
    errors = []

    for src in files:
        rel = src.relative_to(input_dir)
        # Preserve directory structure; force .jpg extension
        dst = output_dir / rel.with_suffix('.jpg')
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            orig_size = src.stat().st_size

            with Image.open(src) as img:
                # Flatten transparency onto white (JPEG has no alpha)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGBA')
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[-1])
                    img = bg
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                img.save(
                    dst,
                    format='JPEG',
                    quality=quality,
                    optimize=True,
                    progressive=True,
                )

            new_size = dst.stat().st_size
            ratio = new_size / orig_size if orig_size else 0.0
            saved_pct = (1 - ratio) * 100

            total_orig += orig_size
            total_new += new_size
            ok_count += 1

            print(
                f"{str(rel):<{name_w}}  "
                f"{_fmt(orig_size):>12}  "
                f"{_fmt(new_size):>12}  "
                f"{saved_pct:>9.1f}%  "
                f"{ratio:>7.3f}"
            )

        except Exception as e:
            errors.append((src, e))
            print(f"{str(rel):<{name_w}}  ERROR: {e}", file=sys.stderr)

    # Summary
    print('-' * len(header))
    if total_orig:
        overall_ratio = total_new / total_orig
        overall_saved = (1 - overall_ratio) * 100
    else:
        overall_ratio = 1.0
        overall_saved = 0.0

    print(
        f"{'TOTAL (' + str(ok_count) + ' files)':<{name_w}}  "
        f"{_fmt(total_orig):>12}  "
        f"{_fmt(total_new):>12}  "
        f"{overall_saved:>9.1f}%  "
        f"{overall_ratio:>7.3f}"
    )

    if errors:
        print(f"\n{len(errors)} file(s) failed:", file=sys.stderr)
        for src, err in errors:
            print(f"  {src}: {err}", file=sys.stderr)

    return {
        "files": ok_count,
        "errors": len(errors),
        "total_original": total_orig,
        "total_reencoded": total_new,
        "ratio": overall_ratio,
        "quality": quality,
    }


def _fmt(n):
    """Human-readable byte size."""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != 'B' else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Bulk re-encode images as JPEG.")
    ap.add_argument("input_dir")
    ap.add_argument("output_dir")
    ap.add_argument("-q", "--quality", type=int, default=85,
                    help="JPEG quality (1-100, default 85)")
    args = ap.parse_args()

    bulk_reencode(args.input_dir, args.output_dir, args.quality)