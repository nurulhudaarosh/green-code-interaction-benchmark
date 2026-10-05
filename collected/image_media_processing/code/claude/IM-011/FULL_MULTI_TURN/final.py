import json
import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError

MEDIUM_MIN = 640    # inclusive: max_dim == 640 is medium
MEDIUM_MAX = 1920   # inclusive: max_dim == 1920 is medium


def _bucket(width: int, height: int) -> str:
    longest = max(width, height)
    if longest < MEDIUM_MIN:
        return "small"
    if longest <= MEDIUM_MAX:
        return "medium"
    return "large"


def _unique_path(dest: Path) -> Path:
    """Return dest, or dest with _1, _2, ... appended if it already exists."""
    if not dest.exists():
        return dest
    n = 1
    while True:
        candidate = dest.with_name(f"{dest.stem}_{n}{dest.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def organize_by_resolution(input_dir, output_dir, recursive=False):
    """
    Copy images from input_dir into output_dir/{small,medium,large}/ based on
    max(width, height):
        small  : < 640
        medium : 640 - 1920 (both ends inclusive)
        large  : > 1920

    Also writes output_dir/manifest.json: a list with one entry per processed
    image, e.g.
        {"filename": "cat.jpg", "bucket": "small", "source": "pets/cat.jpg"}
    "filename" is the name the file was saved under inside its bucket folder
    (it differs from the original only if a name collision got a numeric
    suffix); "source" is the original path relative to input_dir.

    Non-image and unreadable files are skipped. Returns a dict of counts per
    bucket.
    """
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    counts = {"small": 0, "medium": 0, "large": 0}
    for name in counts:
        (output_dir / name).mkdir(parents=True, exist_ok=True)

    manifest = []
    files = input_dir.rglob("*") if recursive else input_dir.iterdir()
    for path in sorted(files):
        if not path.is_file():
            continue
        # Don't re-process files already placed in the output tree
        if output_dir.resolve() in path.resolve().parents:
            continue
        try:
            with Image.open(path) as img:  # reads header only, not full pixels
                width, height = img.size
        except (UnidentifiedImageError, OSError):
            continue

        bucket = _bucket(width, height)
        dest = _unique_path(output_dir / bucket / path.name)
        shutil.copy2(path, dest)
        counts[bucket] += 1
        manifest.append(
            {
                "filename": dest.name,
                "bucket": bucket,
                "source": path.relative_to(input_dir).as_posix(),
            }
        )

    with open(output_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return counts


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        sys.exit("Usage: python organize_by_resolution.py <input_dir> <output_dir>")
    print(organize_by_resolution(sys.argv[1], sys.argv[2]))