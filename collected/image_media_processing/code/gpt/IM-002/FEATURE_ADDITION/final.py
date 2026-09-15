from pathlib import Path
from PIL import Image


def generate_thumbnails(
    input_dir,
    cache_dir,
    max_dim=128,
    extensions=None
):
    input_dir = Path(input_dir)
    cache_dir = Path(cache_dir)

    if extensions is None:
        extensions = [".png", ".jpg", ".jpeg"]

    # Normalize extensions to lowercase and ensure they start with '.'
    valid_extensions = {
        ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for ext in extensions
    }

    cache_dir.mkdir(parents=True, exist_ok=True)

    for src in input_dir.rglob("*"):
        if not src.is_file() or src.suffix.lower() not in valid_extensions:
            continue

        # Mirror the input directory structure
        relative_path = src.relative_to(input_dir)
        dst = cache_dir / relative_path
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(src) as img:
                # Preserves aspect ratio; longest side <= max_dim
                img.thumbnail(
                    (max_dim, max_dim),
                    Image.Resampling.LANCZOS
                )

                img.save(dst)

        except (OSError, Image.UnidentifiedImageError):
            # Skip invalid/corrupt image files
            continue