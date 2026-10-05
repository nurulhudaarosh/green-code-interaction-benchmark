from pathlib import Path
import numpy as np
from PIL import Image


def analyze_brightness(
    input_dir: str | Path,
    dark_threshold: float = 85.0,
    bright_threshold: float = 170.0,
    custom_thresholds: tuple[float, float] | None = None,
) -> list[dict]:
    """Analyzes brightness metrics for all valid images in a directory using PIL 'L' mode.

    Args:
        input_dir: Path to directory containing images.
        dark_threshold: Grayscale mean threshold below which an image is 'dark'.
        bright_threshold: Grayscale mean threshold above which an image is 'bright'.
        custom_thresholds: Optional (dark_max, bright_min) tuple overriding
          dark_threshold and bright_threshold.

    Returns:
        A list of dictionaries with image stats and classification.
    """
    # Override individual thresholds if custom_thresholds is passed
    if custom_thresholds is not None:
        dark_max, bright_min = custom_thresholds
    else:
        dark_max, bright_min = dark_threshold, bright_threshold

    if dark_max > bright_min:
        raise ValueError(
            f"dark threshold ({dark_max}) cannot be greater than bright threshold ({bright_min})"
        )

    path = Path(input_dir)
    if not path.is_dir():
        raise ValueError(f"Directory non-existent or invalid: {input_dir}")

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    results = []

    for file_path in sorted(path.iterdir()):
        if file_path.suffix.lower() not in valid_extensions:
            continue

        try:
            with Image.open(file_path) as img:
                # Ensure RGB mode to handle RGBA/grayscale/palette inputs consistently
                img_rgb = img.convert("RGB")
                arr_rgb = np.array(img_rgb)

                # 1. Per-channel means (RGB)
                r_mean = float(np.mean(arr_rgb[:, :, 0]))
                g_mean = float(np.mean(arr_rgb[:, :, 1]))
                b_mean = float(np.mean(arr_rgb[:, :, 2]))

                # 2. Perceptual luminance using PIL 'L' mode conversion
                img_gray = img_rgb.convert("L")
                grayscale_brightness = float(np.mean(np.array(img_gray)))

                # 3. Classification against effective thresholds
                if grayscale_brightness < dark_max:
                    classification = "dark"
                elif grayscale_brightness > bright_min:
                    classification = "bright"
                else:
                    classification = "normal"

                results.append(
                    {
                        "filename": file_path.name,
                        "path": str(file_path),
                        "means_rgb": {
                            "red": round(r_mean, 2),
                            "green": round(g_green := g_mean, 2),
                            "blue": round(b_mean, 2),
                        },
                        "brightness": round(grayscale_brightness, 2),
                        "classification": classification,
                        "thresholds_used": (dark_max, bright_min),
                    }
                )
        except Exception:
            continue

    return results


# Example Usage
if __name__ == "__main__":
    # Example 1: Using custom thresholds tuple (e.g., stricter dark/bright boundaries)
    stats_custom = analyze_brightness("images", custom_thresholds=(60.0, 190.0))

    for stat in stats_custom:
        print(
            f"[{stat['classification'].upper()}] {stat['filename']} "
            f"(Brightness: {stat['brightness']} | Thresholds: {stat['thresholds_used']})"
        )