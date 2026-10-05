import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError

SMALL_MAX = 640
MEDIUM_MAX = 1920


def _bucket(width: int, height: int) -> str:
    longest = max(width, height)
    if longest <= SMALL_MAX:
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


def organize_by_resolution(input_dir, output_dir):
    """
    Copy images from input_dir into output_dir/{small,medium,large}
    based on max(width, height):

        small:  <= 640
        medium: 641 - 1920
        large:  > 1920

    Only files directly inside input_dir are considered. Files that
    Pillow can't open as images are skipped. Existing files are never
    overwritten; name collisions get a numeric suffix.

    Returns a dict of counts: {"small": n, "medium": n, "large": n, "skipped": n}
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    for name in ("small", "medium", "large"):
        (output_dir / name).mkdir(parents=True, exist_ok=True)

    counts = {"small": 0, "medium": 0, "large": 0, "skipped": 0}

    for path in sorted(input_dir.iterdir()):
        if not path.is_file():
            continue
        try:
            # Image.open is lazy: it reads only the header, not pixel data.
            with Image.open(path) as img:
                width, height = img.size
        except (UnidentifiedImageError, OSError):
            counts["skipped"] += 1
            continue

        bucket = _bucket(width, height)
        dest = _unique_path(output_dir / bucket / path.name)
        shutil.copy2(path, dest)
        counts[bucket] += 1

    return counts


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        sys.exit("Usage: python organize_by_resolution.py INPUT_DIR OUTPUT_DIR")
    print(organize_by_resolution(sys.argv[1], sys.argv[2]))