import os
from pathlib import Path
from PIL import Image, ImageOps


def generate_thumbnails(
    input_dir: str | Path, cache_dir: str | Path, max_dim: int = 128
) -> None:
    """Recursively processes `input_dir` and generates aspect-ratio-preserving

    thumbnails in `cache_dir`, mirroring the original directory structure.
    """
    input_path = Path(input_dir).resolve()
    cache_path = Path(cache_dir).resolve()

    # Supported image extensions
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

    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            # Calculate the mirroring relative path for the thumbnail
            relative_path = file_path.relative_to(input_path)
            thumb_path = cache_path / relative_path

            # Skip generation if thumbnail exists and is newer than the original file
            if thumb_path.exists():
                if thumb_path.stat().st_mtime >= file_path.stat().st_mtime:
                    continue

            # Ensure subdirectories exist
            thumb_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                with Image.open(file_path) as img:
                    # Correct EXIF orientation (e.g., photos taken on phones)
                    img = ImageOps.exif_transpose(img)

                    # Maintain aspect ratio using thumbnail()
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

                    # Convert RGBA/Palette/CMYK to RGB if saving JPEG or handling modes
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


# Example usage:
if __name__ == "__main__":
    generate_thumbnails("path/to/photos", "path/to/cache", max_dim=128)