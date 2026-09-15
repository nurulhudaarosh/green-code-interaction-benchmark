id="58321"
from pathlib import Path
from PIL import Image


def generate_thumbnails(input_dir, cache_dir, max_dim=128):
    """
    Recursively generate aspect-ratio-preserving thumbnails.

    The output directory mirrors the input directory structure.
    Only PNG/JPEG images are processed.

    Returns:
        int: Number of thumbnails generated.
    """
    input_dir = Path(input_dir)
    cache_dir = Path(cache_dir)

    valid_extensions = {".png", ".jpg", ".jpeg"}
    processed_count = 0

    for path in input_dir.rglob("*"):
        # Preserve the directory structure, including empty directories.
        if path.is_dir():
            (cache_dir / path.relative_to(input_dir)).mkdir(
                parents=True, exist_ok=True
            )
            continue

        if path.suffix.lower() not in valid_extensions:
            continue

        output_path = cache_dir / path.relative_to(input_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(path) as img:
                # Preserves aspect ratio and keeps the longest side <= max_dim.
                img.thumbnail(
                    (max_dim, max_dim),
                    Image.Resampling.LANCZOS
                )

                img.save(output_path)
                processed_count += 1

        except (OSError, ValueError):
            # Skip invalid or unreadable image files.
            continue

    return processed_count