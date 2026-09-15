import os
from pathlib import Path
from PIL import Image, ImageOps

def generate_thumbnails(input_dir: str | Path, cache_dir: str | Path, max_dim: int = 128) -> None:
    """
    Recursively generates aspect-ratio-preserving thumbnails for images in input_dir,
    mirroring the directory tree inside cache_dir.
    
    :param input_dir: Path to the directory containing original images.
    :param cache_dir: Path to the destination directory for thumbnails.
    :param max_dim: Maximum bound for the longest side in pixels.
    """
    input_path = Path(input_dir).resolve()
    cache_path = Path(cache_dir).resolve()
    
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}

    if not input_path.exists() or not input_path.is_dir():
        raise ValueError(f"Input directory '{input_dir}' does not exist or is not a directory.")

    for root, _, files in os.walk(input_path):
        rel_path = Path(root).relative_to(input_path)
        target_dir = cache_path / rel_path

        for file_name in files:
            file_path = Path(root) / file_name

            if file_path.suffix.lower() not in valid_extensions:
                continue

            target_file_path = target_dir / file_name

            # Skip generation if thumbnail already exists and is up to date
            if target_file_path.exists() and target_file_path.stat().st_mtime >= file_path.stat().st_mtime:
                continue

            target_dir.mkdir(parents=True, exist_ok=True)

            try:
                with Image.open(file_path) as img:
                    # Correct EXIF rotation (e.g., photos taken on mobile phones)
                    img = ImageOps.exif_transpose(img)
                    
                    # Convert transparent modes to RGB if saving as JPEG
                    if img.mode in ("RGBA", "LA", "P") and target_file_path.suffix.lower() in {".jpg", ".jpeg"}:
                        img = img.convert("RGB")

                    # Fast-loading optimization for JPEG images
                    img.draft(None, (max_dim, max_dim))
                    
                    # Fix: thumbnail() scales down in place while maintaining aspect ratio
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                    
                    img.save(target_file_path, optimize=True)
            except Exception as e:
                print(f"Skipping '{file_path}': {e}")