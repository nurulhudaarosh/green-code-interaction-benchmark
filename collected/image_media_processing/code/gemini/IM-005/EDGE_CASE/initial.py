from pathlib import Path
from PIL import Image, ImageFilter

def apply_blur(input_dir: str, output_dir: str, radius: float) -> None:
    """
    Applies Gaussian blur of the given radius to every image in input_dir 
    and saves the results to output_dir.
    
    :param input_dir: Path to directory containing input images.
    :param output_dir: Path to directory where processed images will be saved.
    :param radius: Blur radius. Must be >= 0. radius=0 acts as a passthrough.
    """
    if radius < 0:
        raise ValueError(f"Radius must be non-negative, got {radius}")
        
    in_path = Path(input_dir)
    out_path = Path(output_dir)
    
    # Ensure output directory exists
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Supported Pillow image extensions
    supported_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
    
    for file_path in in_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            output_file = out_path / file_path.name
            
            with Image.open(file_path) as img:
                # Radius 0 acts as a direct copy/passthrough
                if radius == 0:
                    img.save(output_file)
                else:
                    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=radius))
                    blurred_img.save(output_file)