import os
from pathlib import Path
from PIL import Image

# Map string names to Pillow resample filter constants for convenient lookup
_RESAMPLE_FILTERS = {
    "NEAREST": Image.NEAREST,
    "BILINEAR": Image.BILINEAR,
    "BICUBIC": Image.BICUBIC,
    "LANCZOS": Image.LANCZOS,
}


def batch_resize(input_dir, output_dir, target_size, resample_filter=Image.LANCZOS):
    """
    Resize every PNG/JPEG image in input_dir to target_size and save to output_dir.

    Args:
        input_dir (str): Directory containing source images.
        output_dir (str): Directory to save resized images (created if missing).
        target_size (tuple[int, int]): Desired (width, height) in pixels.
        resample_filter: Resampling filter to use for resizing. Accepts either
            a Pillow constant (e.g. Image.NEAREST, Image.BILINEAR, Image.BICUBIC,
            Image.LANCZOS) or the equivalent string name ("NEAREST", "BILINEAR",
            "BICUBIC", "LANCZOS"), case-insensitive. Defaults to Image.LANCZOS.

    Returns:
        dict: {
            'processed_count': int,  # number of images successfully resized and saved
            'skipped': list[dict],   # entries like {'file': name, 'reason': str}
                                      # for files that failed or were size-mismatched
        }
        An empty/nonexistent input_dir, or one with zero valid image files,
        returns {'processed_count': 0, 'skipped': []} without raising.

    Raises:
        ValueError: If resample_filter is a string that doesn't match a known filter.
    """
    # Normalize string input to the corresponding Pillow constant
    if isinstance(resample_filter, str):
        key = resample_filter.strip().upper()
        if key not in _RESAMPLE_FILTERS:
            raise ValueError(
                f"Unknown resample_filter '{resample_filter}'. "
                f"Choose from: {', '.join(_RESAMPLE_FILTERS.keys())}"
            )
        resample_filter = _RESAMPLE_FILTERS[key]

    valid_exts = {".png", ".jpg", ".jpeg"}
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    processed_count = 0
    skipped = []

    # Missing or non-directory input_dir: treat as "no valid images", don't raise
    if not input_path.is_dir():
        return {"processed_count": 0, "skipped": []}

    output_path.mkdir(parents=True, exist_ok=True)

    # Gather candidate files first so an empty/no-match dir short-circuits cleanly
    candidates = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in valid_exts
    ]

    if not candidates:
        return {"processed_count": 0, "skipped": []}

    for file in candidates:
        try:
            with Image.open(file) as img:
                resized_img = img.resize(target_size, resample_filter)

                # JPEG can't hold alpha/palette — convert before saving
                if file.suffix.lower() in {".jpg", ".jpeg"} and resized_img.mode in ("RGBA", "P"):
                    resized_img = resized_img.convert("RGB")

                dest = output_path / file.name
                resized_img.save(dest)

            # Sanity check: confirm the saved file actually has target_size
            with Image.open(dest) as check_img:
                if check_img.size != tuple(target_size):
                    skipped.append({
                        "file": file.name,
                        "reason": f"size mismatch after save (got {check_img.size}, "
                                  f"expected {tuple(target_size)})"
                    })
                else:
                    processed_count += 1

        except Exception as e:
            skipped.append({"file": file.name, "reason": str(e)})

    return {"processed_count": processed_count, "skipped": skipped}