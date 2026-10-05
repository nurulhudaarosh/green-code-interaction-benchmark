import os
import shutil
from pathlib import Path
from PIL import Image

# Common image file extensions to process
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}

# Thresholds (based on max(width, height))
SMALL_MAX = 640
MEDIUM_MAX = 1920


def organize_by_resolution(input_dir, output_dir):
    """
    Copy images from input_dir into small/medium/large subfolders of output_dir,
    based on max(width, height) thresholds:
        - small  : max(width, height) <= 640
        - medium : 640 < max(width, height) <= 1920
        - large  : max(width, height) > 1920
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")

    # Create output subfolders
    buckets = {
        'small': output_dir / 'small',
        'medium': output_dir / 'medium',
        'large': output_dir / 'large',
    }
    for folder in buckets.values():
        folder.mkdir(parents=True, exist_ok=True)

    copied = {'small': 0, 'medium': 0, 'large': 0}
    skipped = 0

    for entry in input_dir.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        try:
            with Image.open(entry) as img:
                width, height = img.size
        except Exception as e:
            print(f"Skipping {entry.name}: {e}")
            skipped += 1
            continue

        longest = max(width, height)
        if longest <= SMALL_MAX:
            bucket = 'small'
        elif longest <= MEDIUM_MAX:
            bucket = 'medium'
        else:
            bucket = 'large'

        dest = buckets[bucket] / entry.name

        # Avoid overwriting: append a numeric suffix if needed
        counter = 1
        while dest.exists():
            dest = buckets[bucket] / f"{entry.stem}_{counter}{entry.suffix}"
            counter += 1

        shutil.copy2(entry, dest)
        copied[bucket] += 1

    print(
        f"Done. small={copied['small']}, "
        f"medium={copied['medium']}, "
        f"large={copied['large']}, skipped={skipped}"
    )


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python organize_by_resolution.py <input_dir> <output_dir>")
        sys.exit(1)
    organize_by_resolution(sys.argv[1], sys.argv[2])