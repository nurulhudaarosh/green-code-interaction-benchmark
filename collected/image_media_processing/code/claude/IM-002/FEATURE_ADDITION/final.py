import os
from pathlib import Path
from PIL import Image

DEFAULT_EXTS = {".png", ".jpg", ".jpeg"}


def generate_thumbnails(input_dir, cache_dir, max_dim=128, extensions=None):
    """
    Recursively walk `input_dir`, generating aspect-ratio-preserving
    thumbnails (longest side = max_dim) for image files matching
    `extensions`, writing them to `cache_dir` mirroring the same
    relative directory structure.

    Parameters
    ----------
    input_dir : str or Path
        Root directory to search for images.
    cache_dir : str or Path
        Root directory where thumbnails will be written.
    max_dim : int
        Maximum size (in pixels) of the thumbnail's longest side.
    extensions : list[str] or set[str] or None
        File extensions to include (case-insensitive, dot optional,
        e.g. ".png" or "png"). Defaults to {".png", ".jpg", ".jpeg"}.
        Any file whose extension isn't in this set is skipped.

    Returns
    -------
    list[Path]
        Paths of thumbnails that were created.
    """
    input_dir = Path(input_dir)
    cache_dir = Path(cache_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"input_dir does not exist or is not a directory: {input_dir}")

    # Normalize extensions: ensure lowercase and leading dot
    if extensions is None:
        allowed_exts = DEFAULT_EXTS
    else:
        allowed_exts = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in extensions
        }

    created = []

    for root, _dirs, files in os.walk(input_dir):
        root = Path(root)
        rel_root = root.relative_to(input_dir)
        out_root = cache_dir / rel_root

        for fname in files:
            src_path = root / fname
            if src_path.suffix.lower() not in allowed_exts:
                continue

            dst_path = out_root / fname

            try:
                # Skip regeneration if an up-to-date thumbnail already exists
                if dst_path.exists() and dst_path.stat().st_mtime >= src_path.stat().st_mtime:
                    continue

                out_root.mkdir(parents=True, exist_ok=True)

                with Image.open(src_path) as img:
                    if img.mode in ("P", "RGBA", "LA"):
                        img = img.convert("RGB")
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
    # Example usage: defaults to png/jpg/jpeg
    thumbs = generate_thumbnails("photos", "photos_cache", max_dim=128)
    print(f"Generated {len(thumbs)} thumbnails.")

    # Example usage: custom extensions, dot optional, case-insensitive
    thumbs2 = generate_thumbnails(
        "photos", "photos_cache", max_dim=128, extensions=["webp", ".BMP", "gif"]
    )
    print(f"Generated {len(thumbs2)} thumbnails.")