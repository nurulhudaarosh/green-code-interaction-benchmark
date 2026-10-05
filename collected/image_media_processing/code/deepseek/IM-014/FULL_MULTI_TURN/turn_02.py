from pathlib import Path
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


def _to_rgb(img):
    """
    Return an RGB copy of `img`, flattening any transparency onto white.
    Handles RGB, L, P, RGBA, LA, and CMYK source modes safely for JPEG output.
    """
    # Fast path: already RGB with no alpha
    if img.mode == "RGB":
        return img

    # Modes with a real alpha channel we can use as a paste mask
    if img.mode in ("RGBA", "LA"):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg

    # Palette images: convert to RGBA first so transparency (if any) survives,
    # then flatten onto white. If there's no transparency, this still yields RGB.
    if img.mode == "P":
        rgba = img.convert("RGBA")
        # If the palette had no transparent entry, alpha is all 255 — the paste
        # below is then a no-op and we just get the RGB pixels.
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg

    # Everything else (L, CMYK, I, F, etc.): plain convert to RGB
    return img.convert("RGB")


def bulk_reencode(input_dir, output_dir, quality=85):
    """
    Re-encode every image in `input_dir` as JPEG at `quality` (1-100)
    into `output_dir` (mirroring subdirectory structure).

    Every image is converted to RGB before saving, so palette ('P') and
    alpha-channel (RGBA/LA) images are handled without raising OSError.

    Prints per-file original size, re-encoded size, and compression ratio,
    plus a summary at the end. Returns a list of per-file result dicts.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")
    if not (1 <= quality <= 100):
        raise ValueError("quality must be between 1 and 100")

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_in = total_out = 0
    ok = skipped = 0

    for src in sorted(input_dir.rglob("*")):
        if not src.is_file() or src.suffix.lower() not in IMAGE_EXTS:
            continue

        rel = src.relative_to(input_dir)
        dst = output_dir / rel.with_suffix(".jpg")
        dst.parent.mkdir(parents=True, exist_ok=True)

        original_size = src.stat().st_size

        try:
            with Image.open(src) as img:
                img.load()                 # force decode now, inside the try
                rgb = _to_rgb(img)         # <-- guaranteed RGB before save
                rgb.save(dst, "JPEG", quality=quality,
                         optimize=True, progressive=True)
        except Exception as e:
            print(f"  SKIP  {rel}  ({type(e).__name__}: {e})")
            skipped += 1
            continue

        new_size = dst.stat().st_size
        ratio = original_size / new_size if new_size else float("inf")
        saved_pct = (1 - new_size / original_size) * 100 if original_size else 0.0

        total_in += original_size
        total_out += new_size
        ok += 1

        print(
            f"  {str(rel):<50} "
            f"{_fmt(original_size):>10} -> {_fmt(new_size):>10}  "
            f"ratio {ratio:5.2f}x  ({saved_pct:+6.1f}%)"
        )

        results.append({
            "src": str(src),
            "dst": str(dst),
            "original_bytes": original_size,
            "reencoded_bytes": new_size,
            "ratio": ratio,
            "saved_pct": saved_pct,
        })

    print("\n" + "-" * 90)
    if ok:
        overall = total_in / total_out if total_out else float("inf")
        print(
            f"Re-encoded {ok} file(s)  |  "
            f"total {_fmt(total_in)} -> {_fmt(total_out)}  |  "
            f"overall ratio {overall:.2f}x  "
            f"({(1 - total_out / total_in) * 100:+.1f}%)"
        )
    if skipped:
        print(f"Skipped {skipped} file(s)")
    if not ok and not skipped:
        print("No images found.")

    return results


def _fmt(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}B"
        n /= 1024
    return f"{n:.1f}TB"


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python bulk_reencode.py <input_dir> <output_dir> <quality>")
        sys.exit(1)
    bulk_reencode(sys.argv[1], sys.argv[2], int(sys.argv[3]))