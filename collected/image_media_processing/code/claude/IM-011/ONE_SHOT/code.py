import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
SMALL_MAX = 640
MEDIUM_MAX = 1920


def _category(longest_side: int) -> str:
    if longest_side <= SMALL_MAX:
        return "small"
    if longest_side <= MEDIUM_MAX:
        return "medium"
    return "large"


def _unique_path(dest: Path) -> Path:
    """Return dest, or dest with a numeric suffix if it already exists."""
    if not dest.exists():
        return dest
    counter = 1
    while True:
        candidate = dest.with_name(f"{dest.stem}_{counter}{dest.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def organize_by_resolution(input_dir, output_dir):
    """Copy images from input_dir into small/medium/large subfolders of output_dir.

    Classification uses max(width, height):
        small:  <= 640
        medium: 641 - 1920
        large:  > 1920

    Searches input_dir recursively. Unreadable or non-image files are skipped.
    Returns a dict with the number of files copied per category.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    counts = {"small": 0, "medium": 0, "large": 0}
    for name in counts:
        (output_dir / name).mkdir(parents=True, exist_ok=True)

    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        # Don't re-process files already in the output folder
        if output_dir.resolve() in path.resolve().parents:
            continue
        try:
            with Image.open(path) as img:
                width, height = img.size
        except (UnidentifiedImageError, OSError):
            continue

        category = _category(max(width, height))
        dest = _unique_path(output_dir / category / path.name)
        shutil.copy2(path, dest)
        counts[category] += 1

    return counts


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        sys.exit("Usage: python organize_by_resolution.py <input_dir> <output_dir>")
    print(organize_by_resolution(sys.argv[1], sys.argv[2]))