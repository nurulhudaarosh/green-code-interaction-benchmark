from pathlib import Path
from PIL import Image


def generate_thumbnails(
    input_dir,
    cache_dir,
    max_dim=128,
    extensions=None
):
    """
    Recursively generate aspect-ratio-preserving thumbnails.

    Args:
        input_dir: Directory containing the source images.
        cache_dir: Directory where thumbnails will be stored.
        max_dim: Maximum size of the longest thumbnail dimension.
        extensions: Optional iterable of supported extensions.
                    Defaults to PNG/JPEG.

    Returns:
        int: Number of thumbnails successfully generated.
    """
    input_dir = Path(input_dir)
    cache_dir = Path(cache_dir)

    if extensions is None:
        extensions = {".png", ".jpg", ".jpeg"}
    else:
        # Normalize extensions so both "png" and ".png" work.
        extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in extensions
        }

    processed_count = 0

    for path in input_dir.rglob("*"):
        # Mirror the directory structure, including empty directories.
        if path.is_dir():
            (cache_dir / path.relative_to(input_dir)).mkdir(
                parents=True,
                exist_ok=True
            )
            continue

        # Unsupported extensions are simply skipped.
        if path.suffix.lower() not in extensions:
            continue

        output_path = cache_dir / path.relative_to(input_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(path) as img:
                # Preserves aspect ratio; longest side <= max_dim.
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