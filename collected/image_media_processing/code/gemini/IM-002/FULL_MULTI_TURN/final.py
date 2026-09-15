from pathlib import Path
from PIL import Image, ImageOps


def generate_thumbnails(
    input_dir, cache_dir, max_dim=128, extensions=("png", "jpg", "jpeg")
):
    """Recursively generates aspect-ratio-preserving thumbnails,

    mirroring the input directory structure (including empty subdirectories).
    """
    input_path = Path(input_dir).resolve()
    cache_path = Path(cache_dir).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_path}")

    # Normalize extensions to lowercase with a leading dot (e.g., ".png")
    valid_extensions = {
        ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for ext in extensions
    }

    # Step 1: Explicitly mirror all directories (handles empty subdirectories)
    for dir_path in input_path.rglob("*"):
        if dir_path.is_dir():
            relative_dir = dir_path.relative_to(input_path)
            (cache_path / relative_dir).mkdir(parents=True, exist_ok=True)

    # Step 2: Process valid image files
    for file_path in input_path.rglob("*"):
        if not file_path.is_file() or file_path.suffix.lower() not in valid_extensions:
            continue

        relative_path = file_path.relative_to(input_path)
        target_file_path = cache_path / relative_path

        # Skip if thumbnail exists and is up to date
        if (
            target_file_path.exists()
            and target_file_path.stat().st_mtime >= file_path.stat().st_mtime
        ):
            continue

        try:
            with Image.open(file_path) as img:
                img = ImageOps.exif_transpose(img)

                # Preserves aspect ratio in-place within max_dim bounds
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

                save_format = img.format or target_file_path.suffix[1:].upper()
                if save_format in ("JPEG", "JPG") and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                img.save(target_file_path, format=save_format, quality=85)

        except Exception as e:
            print(f"Skipping {file_path}: {e}")