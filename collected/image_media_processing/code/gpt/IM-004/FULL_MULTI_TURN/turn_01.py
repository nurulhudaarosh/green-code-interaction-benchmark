from pathlib import Path
from PIL import Image
import numpy as np


def preprocess_images(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {}

    for file in input_dir.iterdir():
        if not file.is_file():
            continue

        try:
            # Convert image to grayscale
            img = Image.open(file).convert("L")
            arr = np.array(img, dtype=np.float32)

            # Store original min/max
            original_min = float(arr.min())
            original_max = float(arr.max())
            stats[file.name] = {
                "min": original_min,
                "max": original_max
            }

            # Min-max normalization to 0-255
            if original_max == original_min:
                # Flat image: keep it unchanged
                normalized = np.zeros_like(arr, dtype=np.uint8)
                if original_min == 255:
                    normalized.fill(255)
            else:
                normalized = ((arr - original_min) /
                              (original_max - original_min) * 255).astype(np.uint8)

            # Save as PNG
            output_path = output_dir / f"{file.stem}.png"
            Image.fromarray(normalized).save(output_path, format="PNG")

        except Exception as e:
            print(f"Skipping {file.name}: {e}")

    return stats