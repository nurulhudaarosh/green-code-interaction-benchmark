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

    Empty directories are mirrored in the cache directory.
    Unsupported file extensions are skipped.

    Args:
        input_dir: Source directory containing images.
        cache_dir: Destination directory for thumbnails.
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
        extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in extensions
        }

    # Handle a missing or empty input directory safely.
    if not input_dir.exists() or not input_dir.is_dir():
        return 0

    processed_count = 0

    # Create the root cache directory.
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Recursively traverse the entire tree.
    for path in input_dir.rglob("*"):
        relative_path = path.relative_to(input_dir)
        output_path = cache_dir / relative_path

        if path.is_dir():
            # Always mirror directories, including empty ones.
            output_path.mkdir(parents=True, exist_ok=True)
            continue

        # Skip unsupported extensions.
        if path.suffix.lower() not in extensions:
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(path) as img:
                # Preserve aspect ratio and keep the longest side <= max_dim.
                img.thumbnail(
                    (max_dim, max_dim),
                    Image.Resampling.LANCZOS
                )

                img.save(output_path)
                processed_count += 1

        except (OSError, ValueError):
            # Ignore invalid or unreadable image files.
            continue

    return processed_count