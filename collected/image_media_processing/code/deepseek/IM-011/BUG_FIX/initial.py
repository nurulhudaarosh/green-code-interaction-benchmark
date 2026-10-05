import os
import shutil
from pathlib import Path
from PIL import Image

def organize_by_resolution(input_dir, output_dir):
    """
    Copy images from input_dir into small/medium/large subfolders of output_dir
    based on max(width, height) thresholds:
        - small:  max(w, h) <= 640
        - medium: 640 < max(w, h) <= 1920
        - large:  max(w, h) > 1920
    
    Args:
        input_dir (str): Directory containing source images.
        output_dir (str): Directory where small/medium/large subfolders will be created.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")
    
    # Create subfolders
    categories = ("small", "medium", "large")
    for category in categories:
        (output_dir / category).mkdir(parents=True, exist_ok=True)
    
    # Common image extensions
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    
    counts = {c: 0 for c in categories}
    skipped = 0
    
    for file_path in input_dir.iterdir():
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in image_extensions:
            continue
        
        try:
            with Image.open(file_path) as img:
                width, height = img.size
        except Exception as e:
            print(f"Skipping {file_path.name}: {e}")
            skipped += 1
            continue
        
        max_dim = max(width, height)
        
        if max_dim <= 640:
            category = "small"
        elif max_dim <= 1920:
            category = "medium"
        else:
            category = "large"
        
        dest = output_dir / category / file_path.name
        # Avoid overwriting if a file with the same name exists
        if dest.exists():
            stem, suffix = file_path.stem, file_path.suffix
            i = 1
            while dest.exists():
                dest = output_dir / category / f"{stem}_{i}{suffix}"
                i += 1
        
        shutil.copy2(file_path, dest)
        counts[category] += 1
    
    print(f"Organized: small={counts['small']}, "
          f"medium={counts['medium']}, large={counts['large']}, "
          f"skipped={skipped}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python organize.py <input_dir> <output_dir>")
        sys.exit(1)
    organize_by_resolution(sys.argv[1], sys.argv[2])