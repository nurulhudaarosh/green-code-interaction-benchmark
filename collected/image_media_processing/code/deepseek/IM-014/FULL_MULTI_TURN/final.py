from pathlib import Path
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


def _to_rgb(img):
    """Return an RGB copy of `img`, flattening transparency onto white."""
    if img.mode == "RGB":
        return img

    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg

    return img.convert("RGB")


def bulk_reencode(input_dir, output_dir, quality=85):
    """
    Re-encode every image in `input_dir` as JPEG at `quality` (1-100)
    into `output_dir` (mirroring subdirectory structure).

    Handles palette/alpha images (converted to RGB first) and degenerate
    sizes such as 1x1 pixels without division errors.

    Returns a list of per-file result dicts followed by a single
    '__summary__' entry with aggregate totals.
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
                img.load()                       # surface decode errors here
                w, h = img.size                  # may be (1, 1) — that's fine
                rgb = _to_rgb(img)               # guaranteed RGB, any size
                rgb.save(dst, "JPEG", quality=quality,
                         optimize=True, progressive=True)
        except Exception as e:
            print(f"  SKIP  {rel}  ({type(e).__name__}: {e})")
            skipped += 1
            continue

        new_size = dst.stat().st_size

        # Guard against a pathological 0-byte output (shouldn't happen for
        # a successful JPEG save, but keeps the ratio math safe).
        if new_size <= 0:
            print(f"  SKIP  {rel}  (empty output written)")
            skipped += 1
            try:
                dst.unlink()
            except OSError:
                pass
            continue

        ratio = original_size / new_size if original_size else float("inf")
        saved_pct = (1 - new_size / original_size) * 100 if original_size else 0.0

        total_in += original_size
        total_out += new_size
        ok += 1

        print(
            f"  {str(rel):<50} "
            f"{_fmt(original_size):>10} -> {_fmt(new_size):>10}  "
            f"ratio {ratio:5.2f}x  ({saved_pct:+6.1f}%)  "
            f"[{w}x{h}]"
        )

        results.append({
            "src": str(src),
            "dst": str(dst),
            "width": w,
            "height": h,
            "original_bytes": original_size,
            "reencoded_bytes": new_size,
            "ratio": ratio,
            "saved_pct": saved_pct,
        })

    overall_ratio = (total_in / total_out) if total_out else float("inf")
    summary = {
        "__summary__": True,
        "total_original_bytes": total_in,
        "total_reencoded_bytes": total_out,
        "overall_ratio": overall_ratio,
        "files_processed": ok,
        "files_skipped": skipped,
    }

    print("\n" + "-" * 90)
    if ok:
        print(
            f"Re-encoded {ok} file(s)  |  "
            f"total {_fmt(total_in)} -> {_fmt(total_out)}  |  "
            f"overall ratio {overall_ratio:.2f}x  "
            f"({(1 - total_out / total_in) * 100:+.1f}%)"
        )
    if skipped:
        print(f"Skipped {skipped} file(s)")
    if not ok and not skipped:
        print("No images found.")

    results.append(summary)
    return results


def _fmt(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}B"
        n /= 1024
    return f"{n:.1f}TB"