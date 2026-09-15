import os
from pathlib import Path
from PIL import Image

# Extensions Pillow can typically handle as images
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"
}


def generate_thumbnails(input_dir, cache_dir, max_dim=128):
    """
    Recursively walk input_dir, and for every image file found, create an
    aspect-ratio-preserving thumbnail (longest side == max_dim) in cache_dir,
    mirroring the input directory's folder structure.

    Args:
        input_dir (str | Path): Root directory to scan for images.
        cache_dir (str | Path): Root directory to write thumbnails into.
        max_dim (int): Max width/height (in pixels) for the thumbnail's
            longest side. Aspect ratio is preserved.

    Returns:
        list[Path]: Paths of thumbnails that were successfully created.
    """
    input_dir = Path(input_dir)
    cache_dir = Path(cache_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"input_dir does not exist: {input_dir}")

    created = []

    for root, _dirs, files in os.walk(input_dir):
        root = Path(root)
        # Path of this subfolder relative to input_dir
        rel_root = root.relative_to(input_dir)
        out_root = cache_dir / rel_root

        for filename in files:
            src_path = root / filename

            if src_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            dest_path = out_root / filename

            try:
                with Image.open(src_path) as img:
                    # Convert modes that don't save well as e.g. JPEG
                    if img.mode in ("P", "RGBA") and dest_path.suffix.lower() in (
                        ".jpg", ".jpeg"
                    ):
                        img = img.convert("RGB")

                    # Image.thumbnail() preserves aspect ratio in-place
                    img.thumbnail((max_dim, max_dim), Image.LANCZOS)

                    out_root.mkdir(parents=True, exist_ok=True)
                    img.save(dest_path)
                    created.append(dest_path)

            except Exception as e:
                print(f"Skipping {src_path}: {e}")

    return created


if __name__ == "__main__":
    thumbs = generate_thumbnails("photos", "photos_cache", max_dim=128)
    print(f"Created {len(thumbs)} thumbnails.")