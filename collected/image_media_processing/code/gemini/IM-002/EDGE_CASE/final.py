import os
from pathlib import Path
from PIL import Image, ImageOps


def generate_thumbnails(
    input_dir: str | Path, cache_dir: str | Path, max_dim: int = 128
) -> None:
    """Recursively processes `input_dir` and generates aspect-ratio-preserving

    thumbnails in `cache_dir`, mirroring the entire directory structure
    including subdirectories with zero images.
    """
    input_path = Path(input_dir).resolve()
    cache_path = Path(cache_dir).resolve()

    valid_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
        ".tiff",
        ".gif",
    }

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_path}")

    for root, dirs, files in os.walk(input_path):
        current_dir = Path(root)
        relative_dir = current_dir.relative_to(input_path)
        target_dir = cache_path / relative_dir

        # Ensure directory (even if empty of images) is created in cache
        target_dir.mkdir(parents=True, exist_ok=True)

        for file_name in files:
            file_path = current_dir / file_name

            if file_path.suffix.lower() not in valid_extensions:
                continue

            thumb_path = target_dir / file_name

            # Skip generation if thumbnail exists and is newer than original file
            if thumb_path.exists():
                if thumb_path.stat().st_mtime >= file_path.stat().st_mtime:
                    continue

            try:
                with Image.open(file_path) as img:
                    # Correct EXIF orientation
                    img = ImageOps.exif_transpose(img)

                    # Maintain aspect ratio
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

                    # Convert RGBA/Palette/CMYK to RGB for JPEGs
                    if (
                        img.mode in ("RGBA", "LA", "P")
                        and thumb_path.suffix.lower() in [".jpg", ".jpeg"]
                    ):
                        img = img.convert("RGB")
                    elif img.mode == "CMYK":
                        img = img.convert("RGB")

                    # Save the thumbnail
                    img.save(thumb_path)

            except Exception as e:
                print(f"Failed to process {file_path}: {e}")