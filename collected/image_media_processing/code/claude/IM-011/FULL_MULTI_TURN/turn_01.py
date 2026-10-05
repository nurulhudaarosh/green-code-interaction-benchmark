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


def organize_by_resolution(input_dir, output_dir, recursive=False):
    """
    Copy images from input_dir into output_dir/{small,medium,large}/ based on
    max(width, height):
        small  : <= 640
        medium : 641 - 1920
        large  : > 1920

    Non-image and unreadable files are skipped. Name collisions get a numeric
    suffix rather than overwriting. Returns a dict of counts per bucket.
    """
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    counts = {"small": 0, "medium": 0, "large": 0}
    for name in counts:
        (output_dir / name).mkdir(parents=True, exist_ok=True)

    files = input_dir.rglob("*") if recursive else input_dir.iterdir()
    for path in files:
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
        shutil.copy2(path, _unique_path(output_dir / bucket / path.name))
        counts[bucket] += 1

    return counts


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        sys.exit("Usage: python organize_by_resolution.py <input_dir> <output_dir>")
    print(organize_by_resolution(sys.argv[1], sys.argv[2]))