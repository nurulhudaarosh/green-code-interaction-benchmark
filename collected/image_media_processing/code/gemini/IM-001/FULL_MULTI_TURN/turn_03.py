from pathlib import Path
from typing import Literal
from PIL import Image

FilterType = Literal["NEAREST", "BILINEAR", "BICUBIC", "LANCZOS"] | Image.Resampling

RESAMPLE_FILTERS: dict[str, Image.Resampling] = {
    "NEAREST": Image.Resampling.NEAREST,
    "BILINEAR": Image.Resampling.BILINEAR,
    "BICUBIC": Image.Resampling.BICUBIC,
    "LANCZOS": Image.Resampling.LANCZOS,
}

def batch_resize(
    input_dir: str | Path,
    output_dir: str | Path,
    target_size: tuple[int, int],
    resample_filter: FilterType = "LANCZOS",
) -> int:
    """
    Resizes all PNG and JPEG images in input_dir to target_size using the chosen
    resample filter and saves the results to output_dir.

    Args:
        input_dir: Path to directory containing source images.
        output_dir: Path to directory where resized images will be saved.
        target_size: Target dimensions as (width, height).
        resample_filter: Resampling algorithm to use. Accepts string names 
            ('NEAREST', 'BILINEAR', 'BICUBIC', 'LANCZOS') or `Image.Resampling` enums.
            Defaults to 'LANCZOS'.

    Returns:
        int: Number of successfully processed images.
    """
    # Resolve the resample filter argument
    if isinstance(resample_filter, str):
        filter_key = resample_filter.upper()
        if filter_key not in RESAMPLE_FILTERS:
            raise ValueError(
                f"Unsupported filter '{resample_filter}'. "
                f"Choose from: {', '.join(RESAMPLE_FILTERS.keys())}"
            )
        resolved_filter = RESAMPLE_FILTERS[filter_key]
    elif isinstance(resample_filter, Image.Resampling):
        resolved_filter = resample_filter
    else:
        raise TypeError(
            f"Expected resample_filter to be a string or Image.Resampling enum, "
            f"got {type(resample_filter).__name__}"
        )

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    valid_extensions = {".png", ".jpg", ".jpeg"}
    processed_count = 0

    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            try:
                with Image.open(file_path) as img:
                    resized_img = img.resize(target_size, resample=resolved_filter)

                    # Strip transparency/alpha channel if writing to JPEG
                    out_ext = file_path.suffix.lower()
                    if out_ext in {".jpg", ".jpeg"} and resized_img.mode in ("RGBA", "LA", "P"):
                        resized_img = resized_img.convert("RGB")

                    destination = output_path / file_path.name
                    resized_img.save(destination)
                    processed_count += 1
            except Exception as e:
                print(f"Skipping {file_path.name} due to error: {e}")

    return processed_count