import json
import numpy as np
from PIL import Image
from pathlib import Path


def preprocess_images(
    input_dir,
    output_dir,
    flat_value=0,
    clip_percentile=None,
    save_stats=True,
):
    """
    Grayscale and min-max normalize every image in input_dir to full 0-255 range.
    Saves normalized images as PNG in output_dir.

    Args:
        input_dir (str | Path): Directory containing source images.
        output_dir (str | Path): Directory to save normalized PNGs.
        flat_value (int): Pixel value assigned to flat (max == min) images.
            Default 0 (black). Use 127 for mid-gray.
        clip_percentile (float | tuple | None):
            - None: use raw min/max (no clipping).
            - float p in [0, 50): symmetric clip of p% from both tails,
              i.e. anchor at the [p, 100-p] percentile range.
            - (lo, hi) tuple with 0 <= lo < hi <= 100: explicit bounds,
              e.g. (1, 99) or (2, 98).
        save_stats (bool): If True, writes 'stats.json' into output_dir.

    Returns:
        (stats, summary) where:
            stats: {relative_output_path: {
                'source', 'original_min', 'original_max',
                'clip_lo', 'clip_hi', 'flat'}}
            summary: aggregate counts across the batch.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not 0 <= flat_value <= 255:
        raise ValueError("flat_value must be in [0, 255]")

    lo_pct, hi_pct = _parse_clip_percentile(clip_percentile)

    valid_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp', '.gif'}
    stats = {}
    n_processed = n_flat = n_clipped = 0

    for src_path in sorted(input_dir.rglob('*')):
        if not src_path.is_file() or src_path.suffix.lower() not in valid_exts:
            continue

        with Image.open(src_path) as img:
            arr = np.asarray(img.convert('L'), dtype=np.uint8)

        orig_min = int(arr.min())
        orig_max = int(arr.max())

        # Effective anchor values (percentile-clipped or raw extrema)
        if lo_pct is None:
            clip_lo, clip_hi = orig_min, orig_max
        else:
            clip_lo, clip_hi = _percentile_bounds(arr, lo_pct, hi_pct)

        is_flat = (clip_hi == clip_lo)

        if is_flat:
            norm = np.full(arr.shape, flat_value, dtype=np.uint8)
        else:
            span = float(clip_hi - clip_lo)  # guaranteed > 0
            norm = (arr.astype(np.float32) - clip_lo) / span
            norm = np.clip(norm * 255.0, 0, 255).astype(np.uint8)

        rel = src_path.relative_to(input_dir)
        out_name = rel.with_suffix('.png')
        out_path = output_dir / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(norm, mode='L').save(out_path, format='PNG')

        stats[str(out_name)] = {
            'source': str(rel),
            'original_min': orig_min,
            'original_max': orig_max,
            'clip_lo': None if lo_pct is None else int(clip_lo),
            'clip_hi': None if lo_pct is None else int(clip_hi),
            'flat': is_flat,
        }

        n_processed += 1
        n_flat += int(is_flat)
        n_clipped += int(
            lo_pct is not None and (clip_lo > orig_min or clip_hi < orig_max)
        )

    summary = {
        'processed': n_processed,
        'flat': n_flat,
        'clipped': n_clipped,
        'clip_percentile': None if lo_pct is None else [lo_pct, hi_pct],
        'flat_value': flat_value,
    }

    if save_stats:
        with open(output_dir / 'stats.json', 'w') as f:
            json.dump({'summary': summary, 'files': stats}, f, indent=2)

    return stats, summary


def _parse_clip_percentile(clip_percentile):
    """Normalize clip_percentile into a (lo_pct, hi_pct) tuple, or (None, None)."""
    if clip_percentile is None:
        return None, None

    if isinstance(clip_percentile, (int, float)):
        p = float(clip_percentile)
        if not (0 <= p < 50):
            raise ValueError(
                f"clip_percentile as a scalar must be in [0, 50), got {p}"
            )
        return p, 100.0 - p

    if isinstance(clip_percentile, (tuple, list)):
        if len(clip_percentile) != 2:
            raise ValueError(
                "clip_percentile as a sequence must have exactly 2 elements"
            )
        lo, hi = float(clip_percentile[0]), float(clip_percentile[1])
        if not (0 <= lo < hi <= 100):
            raise ValueError(
                f"clip_percentile bounds must satisfy 0 <= lo < hi <= 100, "
                f"got ({lo}, {hi})"
            )
        return lo, hi

    raise TypeError(
        "clip_percentile must be None, a number in [0, 50), or a (lo, hi) pair"
    )


def _percentile_bounds(arr, lo_pct, hi_pct):
    """
    Integer pixel-value anchors for the given percentiles.
    Falls back to raw extrema if rounding collapses the range.
    """
    lo_val, hi_val = np.percentile(arr, [lo_pct, hi_pct])
    lo_val = int(np.round(lo_val))
    hi_val = int(np.round(hi_val))

    if hi_val <= lo_val:
        lo_val = int(arr.min())
        hi_val = int(arr.max())

    return lo_val, hi_val


if __name__ == '__main__':
    stats, summary = preprocess_images(
        'input_images',
        'output_images',
        clip_percentile=(1, 99),
    )
    print(json.dumps(summary, indent=2))