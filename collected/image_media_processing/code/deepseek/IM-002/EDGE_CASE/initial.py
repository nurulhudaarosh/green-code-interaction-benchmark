import os
from PIL import Image
from pathlib import Path
from tqdm import tqdm

def generate_thumbnails(input_dir, cache_dir, max_dim=128, show_progress=True):
    """
    Recursively creates aspect-ratio-preserving thumbnails mirroring the input directory tree.
    Includes progress tracking and detailed logging.
    """
    input_path = Path(input_dir)
    cache_path = Path(cache_dir)
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico'}
    
    # Collect all image files first for progress tracking
    all_images = []
    def collect_images(directory):
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    collect_images(item)
                elif item.is_file() and item.suffix.lower() in image_extensions:
                    all_images.append(item)
        except PermissionError:
            print(f"Permission denied: {directory}")
    
    collect_images(input_path)
    
    if show_progress:
        print(f"Found {len(all_images)} images to process")
        iterator = tqdm(all_images, desc="Creating thumbnails")
    else:
        iterator = all_images
    
    processed = 0
    skipped = 0
    errors = 0
    
    for image_path in iterator:
        # Calculate relative path and cache path
        rel_path = image_path.relative_to(input_path)
        output_path = cache_path / rel_path
        
        # Check if we need to process this image
        if output_path.exists():
            if output_path.stat().st_mtime >= image_path.stat().st_mtime:
                skipped += 1
                continue
        
        # Create thumbnail
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with Image.open(image_path) as img:
                # Handle transparency
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                
                # Determine save format
                if image_path.suffix.lower() in {'.jpg', '.jpeg'}:
                    img.save(output_path, 'JPEG', quality=85, optimize=True)
                elif image_path.suffix.lower() == '.png':
                    img.save(output_path, 'PNG', optimize=True)
                else:
                    img.save(output_path, quality=85, optimize=True)
                
                processed += 1
                
        except Exception as e:
            errors += 1
            if show_progress:
                tqdm.write(f"Error processing {image_path}: {e}")
    
    # Summary
    print(f"\n✅ Summary:")
    print(f"  - Processed: {processed}")
    print(f"  - Skipped (up to date): {skipped}")
    print(f"  - Errors: {errors}")
    print(f"  - Total: {len(all_images)}")

# Example usage:
if __name__ == "__main__":
    generate_thumbnails(
        input_dir="/path/to/images",
        cache_dir="/path/to/thumbnails",
        max_dim=128,
        show_progress=True
    )