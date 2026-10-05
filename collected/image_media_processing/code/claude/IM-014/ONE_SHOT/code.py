"""Bulk re-encode images as JPEG and report size savings.

Requires: Pillow  (pip install pillow)
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def _to_rgb(img: Image.Image) -> Image.Image:
    """Convert to RGB, flattening any transparency onto white (JPEG has no alpha)."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return img.convert("RGB") if img.mode != "RGB" else img


def _fmt_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


def bulk_reencode(input_dir, output_dir, quality=85):
    """Re-encode every image under input_dir as JPEG into output_dir.

    - Recurses into subdirectories and mirrors the folder structure.
    - Prints original size, re-encoded size, and compression ratio per file
      (ratio = original / reencoded, so >1 means the file got smaller).
    - Returns a list of per-file result dicts (failures have an "error" key).

    Args:
        input_dir:  directory containing source images.
        output_dir: directory to write .jpg files to (created if needed).
        quality:    JPEG quality, 1-100.
    """
    input_dir, output_dir = Path(input_dir).resolve(), Path(output_dir).resolve()
    if not input_dir.is_dir():
        raise NotADirectoryError(f"input_dir not found: {input_dir}")
    if not 1 <= int(quality) <= 100:
        raise ValueError("quality must be between 1 and 100")
    quality = int(quality)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = sorted(
        p for p in input_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTS
        and output_dir not in p.parents  # don't re-process our own output
    )

    results, used_outputs = [], set()
    rows = []

    for src in sources:
        rel = src.relative_to(input_dir)
        dest = output_dir / rel.with_suffix(".jpg")
        # a.png and a.jpeg would both map to a.jpg: disambiguate the later one
        if dest in used_outputs:
            dest = dest.with_name(f"{src.stem}_{src.suffix.lstrip('.').lower()}.jpg")
        used_outputs.add(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(src) as img:
                img = ImageOps.exif_transpose(img)  # honor camera rotation
                icc = img.info.get("icc_profile")
                rgb = _to_rgb(img)
                save_kwargs = {"format": "JPEG", "quality": quality, "optimize": True}
                if icc:
                    save_kwargs["icc_profile"] = icc
                rgb.save(dest, **save_kwargs)
            orig, new = src.stat().st_size, dest.stat().st_size
            ratio = orig / new if new else float("inf")
            results.append({"file": str(rel), "output": str(dest),
                            "original_bytes": orig, "reencoded_bytes": new,
                            "ratio": ratio})
            rows.append((str(rel), _fmt_size(orig), _fmt_size(new), f"{ratio:.2f}x"))
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            results.append({"file": str(rel), "error": str(exc)})
            rows.append((str(rel), "-", "-", f"FAILED: {exc}"))

    # ---- report ----
    if not rows:
        print(f"No images found in {input_dir}")
        return results

    header = ("File", "Original", "Re-encoded", "Ratio")
    widths = [max(len(r[i]) for r in rows + [header]) for i in range(3)]
    fmt = f"{{:<{widths[0]}}}  {{:>{widths[1]}}}  {{:>{widths[2]}}}  {{}}"
    print(fmt.format(*header))
    print("-" * (sum(widths) + 8 + 8))
    for row in rows:
        print(fmt.format(*row))

    ok = [r for r in results if "error" not in r]
    failed = len(results) - len(ok)
    if ok:
        total_orig = sum(r["original_bytes"] for r in ok)
        total_new = sum(r["reencoded_bytes"] for r in ok)
        print("-" * (sum(widths) + 8 + 8))
        print(fmt.format(f"TOTAL ({len(ok)} files)", _fmt_size(total_orig),
                         _fmt_size(total_new), f"{total_orig / total_new:.2f}x"))
    if failed:
        print(f"{failed} file(s) failed.")
    return results


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Bulk re-encode images as JPEG.")
    ap.add_argument("input_dir")
    ap.add_argument("output_dir")
    ap.add_argument("-q", "--quality", type=int, default=85)
    args = ap.parse_args()
    bulk_reencode(args.input_dir, args.output_dir, args.quality)