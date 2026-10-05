"""Bulk re-encode images as JPEG. Requires: pip install Pillow"""
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError


def _human(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024


def bulk_reencode(input_dir, output_dir, quality=80):
    """Re-encode every image under input_dir as JPEG in output_dir.

    - Recurses into subfolders and mirrors the structure.
    - Non-image files are skipped silently.
    - Transparency is flattened onto white (JPEG has no alpha).
    - EXIF orientation is applied before saving.
    - Returns a dict keyed by relative input path, one result dict per file
      (or {"file", "error"} on failure), plus a "__summary__" entry:
      {"file_count", "original_bytes", "reencoded_bytes", "ratio"}.
      Totals cover successfully processed files only.
    """
    if not 1 <= quality <= 100:
        raise ValueError("quality must be between 1 and 100")

    in_dir = Path(input_dir).resolve()
    out_dir = Path(output_dir).resolve()
    if not in_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {in_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    results, used = [], set()

    for src in sorted(p for p in in_dir.rglob("*") if p.is_file()):
        if out_dir in src.parents:  # output nested inside input: don't re-process it
            continue

        rel = src.relative_to(in_dir)
        dest = out_dir / rel.with_suffix(".jpg")
        if dest in used:  # e.g. a.png and a.gif would both map to a.jpg
            dest = dest.with_name(f"{rel.stem}_{src.suffix.lstrip('.').lower()}.jpg")

        try:
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im)
                if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                    im = im.convert("RGBA")
                    flat = Image.new("RGB", im.size, "white")
                    flat.paste(im, mask=im.getchannel("A"))
                    im = flat
                elif im.mode != "RGB":
                    im = im.convert("RGB")

                dest.parent.mkdir(parents=True, exist_ok=True)
                im.save(dest, "JPEG", quality=quality, optimize=True)
        except UnidentifiedImageError:
            continue  # not an image
        except Exception as exc:
            results.append({"file": str(rel), "error": str(exc)})
            continue

        used.add(dest)
        orig, new = src.stat().st_size, dest.stat().st_size
        results.append({
            "file": str(rel),
            "output": str(dest),
            "original_bytes": orig,
            "reencoded_bytes": new,
            "ratio": orig / new if new else float("inf"),
        })

    summary = _summarize(results)
    _report(results, summary, quality)

    report = {r["file"]: r for r in results}
    report["__summary__"] = summary
    return report


def _summarize(results):
    ok = [r for r in results if "error" not in r]
    total_orig = sum(r["original_bytes"] for r in ok)
    total_new = sum(r["reencoded_bytes"] for r in ok)
    return {
        "file_count": len(ok),
        "original_bytes": total_orig,
        "reencoded_bytes": total_new,
        "ratio": total_orig / total_new if total_new else float("inf"),
    }


def _report(results, summary, quality):
    ok = [r for r in results if "error" not in r]
    bad = [r for r in results if "error" in r]

    if ok:
        width = max(len(r["file"]) for r in ok + [{"file": "File"}])
        print(f"{'File':<{width}}  {'Original':>10}  {'Re-encoded':>10}  {'Ratio':>7}")
        print("-" * (width + 33))
        for r in ok:
            print(f"{r['file']:<{width}}  {_human(r['original_bytes']):>10}  "
                  f"{_human(r['reencoded_bytes']):>10}  {r['ratio']:>6.2f}x")

        print("-" * (width + 33))
        print(f"{'TOTAL (' + str(summary['file_count']) + ' files, q=' + str(quality) + ')':<{width}}  "
              f"{_human(summary['original_bytes']):>10}  "
              f"{_human(summary['reencoded_bytes']):>10}  "
              f"{summary['ratio']:>6.2f}x")
    else:
        print("No images found.")

    for r in bad:
        print(f"FAILED: {r['file']}: {r['error']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        sys.exit("usage: python bulk_reencode.py INPUT_DIR OUTPUT_DIR [QUALITY]")
    bulk_reencode(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 80)