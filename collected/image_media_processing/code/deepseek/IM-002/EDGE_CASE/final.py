import os
from PIL import Image
from pathlib import Path

def generate_thumbnails(input_dir, cache_dir, max_dim=128, verbose=False):
    """
    Recursively creates aspect-ratio-preserving thumbnails mirroring the input directory tree.
    
    Args:
        input_dir (str): Path to the source directory containing images
        cache_dir (str): Path to the destination directory for thumbnails
        max_dim (int): Maximum dimension (width or height) for thumbnails. Default 128.
        verbose (bool): If True, prints detailed progress information. Default False.
    """
    input_path = Path(input_dir)
    cache_path = Path(cache_dir)
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico'}
    
    def create_thumbnail(image_path, output_path, max_dim):
        """Create a thumbnail maintaining aspect ratio."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for PNG with alpha, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail using thumbnail method (preserves aspect ratio)
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                
                # Ensure the output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save the thumbnail
                img.save(output_path, quality=85, optimize=True)
                return True
                
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return False
    
    def process_directory(current_input_dir, current_cache_dir):
        """Recursively process directories and create thumbnails."""
        try:
            # Create the cache directory mirror if it doesn't exist
            # This handles empty directories as well
            current_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all items in the current directory
            items = list(current_input_dir.iterdir())
            
            # Count images in this directory (not subdirectories)
            image_files = [item for item in items 
                          if item.is_file() and item.suffix.lower() in image_extensions]
            subdirs = [item for item in items if item.is_dir()]
            
            if verbose:
                if image_files:
                    print(f"📁 {current_input_dir.relative_to(input_path)}: "
                          f"{len(image_files)} images, {len(subdirs)} subdirectories")
                elif subdirs:
                    print(f"📁 {current_input_dir.relative_to(input_path)}: "
                          f"0 images, {len(subdirs)} subdirectories (empty directory)")
                else:
                    print(f"📁 {current_input_dir.relative_to(input_path)}: "
                          f"empty directory")
            
        except PermissionError:
            print(f"Permission denied: {current_input_dir}")
            return
        except Exception as e:
            print(f"Error accessing {current_input_dir}: {e}")
            return
        
        # Process image files in current directory
        for image_path in image_files:
            output_path = current_cache_dir / image_path.name
            
            # Check if thumbnail already exists and is up-to-date
            if output_path.exists():
                if output_path.stat().st_mtime >= image_path.stat().st_mtime:
                    if verbose:
                        print(f"  ✓ Skipping {image_path.name} (up to date)")
                    continue
            
            if verbose:
                print(f"  → Creating thumbnail for {image_path.name}")
            
            create_thumbnail(image_path, output_path, max_dim)
        
        # Recursively process subdirectories
        for subdir in subdirs:
            new_cache_dir = current_cache_dir / subdir.name
            process_directory(subdir, new_cache_dir)
    
    # Start the recursive processing
    if verbose:
        print(f"Starting thumbnail generation...")
        print(f"Input: {input_path}")
        print(f"Cache: {cache_path}")
        print(f"Max dimension: {max_dim}px")
        print("-" * 50)
    
    process_directory(input_path, cache_path)
    
    if verbose:
        print("-" * 50)
        print("✅ Thumbnail generation complete!")

# Example usage:
if __name__ == "__main__":
    # Basic usage
    generate_thumbnails(
        input_dir="/path/to/images",
        cache_dir="/path/to/thumbnails",
        max_dim=128
    )
    
    # With verbose logging
    generate_thumbnails(
        input_dir="/path/to/images",
        cache_dir="/path/to/thumbnails",
        max_dim=128,
        verbose=True
    )