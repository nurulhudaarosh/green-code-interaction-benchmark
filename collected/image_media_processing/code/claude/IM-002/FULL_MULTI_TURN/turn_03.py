import os
from pathlib import Path
from PIL import Image, UnidentifiedImageError

DEFAULT_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def generate_thumbnails(input_dir, cache_dir, max_dim=128, extensions=None):
    """
    Recursively walk `input_dir`, creating aspect-ratio-preserving thumbnails
    (longest side = max_dim) for every image found, mirroring the directory
    structure under `cache_dir`.

    extensions: optional iterable of file extensions to include (e.g.
        [".png", ".webp"] or ["gif"] — leading dots and case are normalized).
        Defaults to {".png", ".jpg", ".jpeg"}. Files with any other extension
        are skipped, as are files with extensions Pillow can't actually open.

    Returns a list of (source_path, thumbnail_path) tuples for files processed.
    """
    input_dir = Path(input_dir)
    cache_dir = Path(cache_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"{input_dir} is not a directory")

    if extensions is None:
        allowed_extensions = DEFAULT_EXTENSIONS
    else:
        allowed_extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in extensions
        }

    results = []

    for root, _dirs, files in os.walk(input_dir):
        root = Path(root)
        rel_root = root.relative_to(input_dir)
        dest_root = cache_dir / rel_root

        for filename in files:
            src_path = root / filename
            if src_path.suffix.lower() not in allowed_extensions:
                continue

            dest_path = dest_root / filename

            try:
                with Image.open(src_path) as img:
                    img = img.convert("RGB") if img.mode in ("P", "RGBA") else img

                    # Preserves aspect ratio; longest side <= max_dim.
                    img.thumbnail((max_dim, max_dim), Image.LANCZOS)

                    dest_root.mkdir(parents=True, exist_ok=True)
                    img.save(dest_path)

                results.append((str(src_path), str(dest_path)))

            except UnidentifiedImageError:
                # Extension was allowed, but Pillow couldn't actually decode it.
                continue
            except OSError as e:
                print(f"Skipping {src_path}: {e}")
                continue

    return results