from pathlib import Path
from PIL import Image


def generate_thumbnails(input_dir, cache_dir, max_dim=128):
    input_dir = Path(input_dir)
    cache_dir = Path(cache_dir)

    cache_dir.mkdir(parents=True, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg"}

    for src in input_dir.rglob("*"):
        if not src.is_file() or src.suffix.lower() not in valid_extensions:
            continue

        # Mirror the input directory tree in the cache directory
        relative_path = src.relative_to(input_dir)
        dst = cache_dir / relative_path
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(src) as img:
                # thumbnail() preserves aspect ratio and limits
                # the longest dimension to max_dim.
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

                # Save the thumbnail
                img.save(dst)

        except (OSError, Image.UnidentifiedImageError):
            # Skip invalid/corrupt image files
            continue