import json
import shutil
from pathlib import Path
from PIL import Image

def organize_by_resolution(input_dir, output_dir):
    """
    Copy images from input_dir into small/medium/large subfolders of output_dir
    based on max(width, height) thresholds of 640 and 1920, and write a
    manifest.json into output_dir listing every processed image and its bucket.
    
    - small:  max(width, height) < 640
    - medium: 640 <= max(width, height) <= 1920
    - large:  max(width, height) > 1920
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output subfolders
    categories = ("small", "medium", "large")
    for category in categories:
        (output_path / category).mkdir(parents=True, exist_ok=True)
    
    # Common image extensions
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    
    copied = {"small": 0, "medium": 0, "large": 0}
    skipped = 0
    manifest = []
    
    for file_path in input_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in image_extensions:
            continue
        
        try:
            with Image.open(file_path) as img:
                width, height = img.size
        except (OSError, ValueError) as e:
            print(f"Skipping {file_path}: {e}")
            skipped += 1
            continue
        
        longest_side = max(width, height)
        
        if longest_side < 640:
            category = "small"
        elif longest_side <= 1920:
            category = "medium"
        else:
            category = "large"
        
        dest = output_path / category / file_path.name
        
        # Handle filename collisions
        if dest.exists():
            stem, suffix = file_path.stem, file_path.suffix
            counter = 1
            while dest.exists():
                dest = output_path / category / f"{stem}_{counter}{suffix}"
                counter += 1
        
        shutil.copy2(file_path, dest)
        copied[category] += 1
        
        manifest.append({
            "filename": dest.name,
            "bucket": category,
            "width": width,
            "height": height,
            "source": str(file_path),
        })
    
    # Write manifest.json
    manifest_path = output_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Copied: {copied['small']} small, {copied['medium']} medium, "
          f"{copied['large']} large. Skipped: {skipped}.")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python organize_by_resolution.py <input_dir> <output_dir>")
        sys.exit(1)
    organize_by_resolution(sys.argv[1], sys.argv[2])