from pathlib import Path
import shutil
from PIL import Image

def organize_by_resolution(input_dir: str | Path, output_dir: str | Path) -> None:
    """
    Copies images from input_dir into 'small', 'medium', or 'large' 
    subfolders in output_dir based on their maximum dimension (width or height).

    Thresholds:
    - small:  max_dim < 640
    - medium: 640 <= max_dim <= 1920
    - large:  max_dim > 1920
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Valid image extensions to process
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".gif"}

    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            try:
                # Open image without loading pixel data into memory
                with Image.open(file_path) as img:
                    max_dim = max(img.width, img.height)

                # Determine destination subfolder
                if max_dim < 640:
                    category = "small"
                elif max_dim <= 1920:
                    category = "medium"
                else:
                    category = "large"

                target_dir = output_path / category
                target_dir.mkdir(parents=True, exist_ok=True)

                # Copy file to category directory
                shutil.copy2(file_path, target_dir / file_path.name)

            except (IOError, SyntaxError) as e:
                print(f"Skipping non-image or corrupt file {file_path.name}: {e}")

# Example Usage:
# organize_by_resolution("path/to/source_images", "path/to/organized_images")