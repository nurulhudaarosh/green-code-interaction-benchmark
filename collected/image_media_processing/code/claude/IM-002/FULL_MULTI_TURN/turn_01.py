import os
from pathlib import Path
from PIL import Image, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}


def generate_thumbnails(input_dir, cache_dir, max_dim=128):
    """
    Recursively walk `input_dir`, creating aspect-ratio-preserving thumbnails
    (longest side = max_dim) for every image found, mirroring the directory
    structure under `cache_dir`.

    Returns a list of (source_path, thumbnail_path) tuples for files processed.
    """
    input_dir = Path(input_dir)
    cache_dir = Path(cache_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"{input_dir} is not a directory")

    results = []

    for root, _dirs, files in os.walk(input_dir):
        root = Path(root)
        rel_root = root.relative_to(input_dir)
        dest_root = cache_dir / rel_root

        for filename in files:
            src_path = root / filename
            if src_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            dest_path = dest_root / filename

            try:
                with Image.open(src_path) as img:
                    img = img.convert("RGB") if img.mode in ("P", "RGBA") else img
                    img.thumbnail((max_dim, max_dim), Image.LANCZOS)

                    dest_root.mkdir(parents=True, exist_ok=True)
                    img.save(dest_path)

                results.append((str(src_path), str(dest_path)))

            except UnidentifiedImageError:
                # Not a valid/readable image despite the extension; skip it.
                continue
            except OSError as e:
                print(f"Skipping {src_path}: {e}")
                continue

    return results