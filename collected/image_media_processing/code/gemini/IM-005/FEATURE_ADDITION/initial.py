import os
from pathlib import Path
from PIL import Image, ImageFilter

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

def apply_blur(input_dir: str | Path, output_dir: str | Path, radius: float) -> None:
    """
    Applies Gaussian blur of a given radius to every image in input_dir
    and saves the results to output_dir.
    
    - radius < 0: Raises ValueError
    - radius == 0: Passes through original images without modification
    """
    if radius < 0:
        raise ValueError("Radius must be non-negative.")
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_path}")
        
    output_path.mkdir(parents=True, exist_ok=True)
    
    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
            with Image.open(file_path) as img:
                if radius > 0:
                    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=radius))
                else:
                    blurred_img = img.copy()
                
                save_destination = output_path / file_path.name
                
                # Preserve original image mode/format during saving
                if img.format:
                    blurred_img.save(save_destination, format=img.format)
                else:
                    blurred_img.save(save_destination)