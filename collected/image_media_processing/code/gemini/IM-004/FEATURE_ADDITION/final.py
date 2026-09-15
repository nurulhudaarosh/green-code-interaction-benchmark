from pathlib import Path
from typing import Dict, Optional, Tuple
import cv2
import numpy as np


def preprocess_images(
    input_dir: str | Path,
    output_dir: str | Path,
    clip_percentile: Optional[float] = None,
) -> Dict[str, Tuple[float, float]]:
    """Grayscales and min-max normalizes images to 0-255 range.

    Parameters
    ----------
    input_dir : str | Path
        Directory containing source images.
    output_dir : str | Path
        Directory where processed PNG images will be saved.
    clip_percentile : float, optional
        Percentile value (e.g., 1.0 for 1st and 99th percentiles) used to clip
        extreme pixel intensities prior to normalization. Must be in range (0,
        50).

    Returns
    -------
    Dict[str, Tuple[float, float]]
        A dictionary mapping each filename to a tuple of (original_min,
        original_max).

    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    supported_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".tiff",
        ".webp",
    }
    stats = {}

    for file_path in input_path.iterdir():
        if (
            file_path.is_file()
            and file_path.suffix.lower() in supported_extensions
        ):
            # Read image as grayscale
            img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            # Record true original stats before any clipping
            orig_min = float(np.min(img))
            orig_max = float(np.max(img))
            stats[file_path.name] = (orig_min, orig_max)

            img_float = img.astype(np.float32)

            # Determine normalization bounds (with percentile clipping if requested)
            if clip_percentile is not None and 0 < clip_percentile < 50:
                p_low = clip_percentile
                p_high = 100.0 - clip_percentile
                min_val = float(np.percentile(img_float, p_low))
                max_val = float(np.percentile(img_float, p_high))
                img_float = np.clip(img_float, min_val, max_val)
            else:
                min_val = orig_min
                max_val = orig_max

            # Min-Max normalization to [0, 255]
            if max_val > min_val:
                normalized = (img_float - min_val) / (max_val - min_val) * 255.0
                normalized = np.clip(normalized, 0, 255).astype(np.uint8)
            else:
                # Handle edge case where clipped min and max are equal
                normalized = np.zeros_like(img, dtype=np.uint8)

            # Save as PNG
            out_file = output_path / f"{file_path.stem}.png"
            cv2.imwrite(str(out_file), normalized)

    return stats