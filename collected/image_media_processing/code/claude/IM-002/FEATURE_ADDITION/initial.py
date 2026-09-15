import os
from pathlib import Path
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}


def generate_thumbnails(input_dir, cache_dir, max_dim=128):
    """
    Recursively walk `input_dir`, generating aspect-ratio-preserving
    thumbnails (longest side = max_dim) for every image file found,
    and write them to `cache_dir` mirroring the same relative directory
    structure.

    Parameters
    ----------
    input_dir : str or Path
        Root directory to search for images.
    cache_dir : str or Path
        Root directory where thumbnails will be written.
    max_dim : int
        Maximum size (in pixels) of the thumbnail's longest side.

    Returns
    -------
    list[Path]
        Paths of thumbnails that were created.
    """
    input_dir = Path(input_dir)
    cache_dir = Path(cache_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"input_dir does not exist or is not a directory: {input_dir}")

    created = []

    for root, _dirs, files in os.walk(input_dir):
        root = Path(root)
        rel_root = root.relative_to(input_dir)
        out_root = cache_dir / rel_root

        for fname in files:
            src_path = root / fname
            if src_path.suffix.lower() not in IMAGE_EXTS:
                continue

            dst_path = out_root / fname

            try:
                # Skip regeneration if an up-to-date thumbnail already exists
                if dst_path.exists() and dst_path.stat().st_mtime >= src_path.stat().st_mtime:
                    continue

                out_root.mkdir(parents=True, exist_ok=True)

                with Image.open(src_path) as img:
                    img = img.convert("RGB") if img.mode in ("P", "RGBA", "LA") else img
                    # Recompute mode-safe convert: preserve alpha where useful
                    thumb = img.copy()
                    thumb.thumbnail((max_dim, max_dim), Image.LANCZOS)
                    thumb.save(dst_path)

                created.append(dst_path)

            except (OSError, ValueError) as e:
                # Not a valid image, or unreadable — skip it, don't crash the whole run
                print(f"Skipping {src_path}: {e}")
                continue

    return created


if __name__ == "__main__":
    # Example usage
    thumbs = generate_thumbnails("photos", "photos_cache", max_dim=128)
    print(f"Generated {len(thumbs)} thumbnails.")