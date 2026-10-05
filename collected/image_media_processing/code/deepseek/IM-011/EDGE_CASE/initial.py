import os
import shutil
from pathlib import Path
from PIL import Image

def organize_by_resolution(input_dir, output_dir):
    """
    Copy images from input_dir into small/medium/large subfolders of output_dir
    based on max(width, height) thresholds of 640 and 1920.
    
    - small:  max(width, height) < 640
    - medium: 640 <= max(width, height) < 1920
    - large:  max(width, height) >= 1920
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    # Create output subfolders
    categories = ("small", "medium", "large")
    for category in categories:
        (output_path / category).mkdir(parents=True, exist_ok=True)
    
    # Supported image extensions
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    
    copied = {"small": 0, "medium": 0, "large": 0}
    skipped = 0
    
    for file_path in input_path.iterdir():
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
        
        longest_side = max(width, height)
        
        if longest_side < 640:
            category = "small"
        elif longest_side < 1920:
            category = "medium"
        else:
            category = "large"
        
        dest = output_path / category / file_path.name
        
        # Avoid overwriting files with the same name
        counter = 1
        while dest.exists():
            dest = output_path / category / f"{file_path.stem}_{counter}{file_path.suffix}"
            counter += 1
        
        shutil.copy2(file_path, dest)
        copied[category] += 1
    
    return {
        "copied": copied,
        "skipped": skipped,
        "total": sum(copied.values()),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_dir> <output_dir>")
        sys.exit(1)
    
    result = organize_by_resolution(sys.argv[1], sys.argv[2])
    print(f"Done. Copied {result['total']} images:")
    for cat, count in result["copied"].items():
        print(f"  {cat}: {count}")
    if result["skipped"]:
        print(f"  skipped (unreadable): {result['skipped']}")