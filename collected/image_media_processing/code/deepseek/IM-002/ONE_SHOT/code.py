import os
import sys
from PIL import Image
from pathlib import Path


def generate_thumbnails(input_dir, cache_dir, max_dim=128):
    """
    Recursively create aspect-ratio-preserving thumbnails mirroring the input directory tree.
    
    Args:
        input_dir (str): Path to the source directory containing images
        cache_dir (str): Path to the destination directory for thumbnails
        max_dim (int): Maximum dimension (width or height) for thumbnails (default: 128)
    
    Returns:
        tuple: (success_count, error_count) - Number of thumbnails created and failed
    """
    
    input_path = Path(input_dir)
    cache_path = Path(cache_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist")
    
    if not input_path.is_dir():
        raise NotADirectoryError(f"'{input_dir}' is not a directory")
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico'}
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    # Walk through the input directory
    for root, dirs, files in os.walk(input_path):
        # Calculate relative path from input directory
        rel_path = Path(root).relative_to(input_path)
        
        # Create corresponding directory in cache
        target_dir = cache_path / rel_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each file in the current directory
        for filename in files:
            file_path = Path(root) / filename
            file_ext = file_path.suffix.lower()
            
            # Skip non-image files
            if file_ext not in image_extensions:
                skipped_count += 1
                continue
            
            # Skip hidden files (optional)
            if filename.startswith('.'):
                skipped_count += 1
                continue
            
            # Generate thumbnail path
            # Keep the same filename but in the cache directory
            thumbnail_path = target_dir / filename
            
            try:
                # Check if thumbnail already exists and is up-to-date
                if thumbnail_path.exists():
                    # Compare modification times
                    if thumbnail_path.stat().st_mtime >= file_path.stat().st_mtime:
                        skipped_count += 1
                        continue
                
                # Create thumbnail
                create_thumbnail(file_path, thumbnail_path, max_dim)
                success_count += 1
                
            except Exception as e:
                print(f"Error creating thumbnail for {file_path}: {str(e)}")
                error_count += 1
    
    # Print summary
    print(f"\n--- Thumbnail Generation Summary ---")
    print(f"Generated: {success_count} thumbnails")
    print(f"Errors: {error_count}")
    print(f"Skipped: {skipped_count} files (non-images, hidden, or up-to-date)")
    print(f"Cache directory: {cache_path}")
    
    return success_count, error_count


def create_thumbnail(image_path, output_path, max_dim):
    """
    Create an aspect-ratio-preserving thumbnail from an image.
    
    Args:
        image_path (Path): Path to source image
        output_path (Path): Path to save thumbnail
        max_dim (int): Maximum dimension (width or height)
    """
    with Image.open(image_path) as img:
        # Convert to RGB if necessary (for formats like PNG with alpha)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate new dimensions preserving aspect ratio
        width, height = img.size
        if width > height:
            new_width = max_dim
            new_height = int(height * (max_dim / width))
        else:
            new_height = max_dim
            new_width = int(width * (max_dim / height))
        
        # Resize the image
        img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save the thumbnail
        img.save(output_path, 'JPEG', quality=85, optimize=True)


def main():
    """Example usage and command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate aspect-ratio-preserving thumbnails mirroring directory structure'
    )
    parser.add_argument('input_dir', help='Source directory containing images')
    parser.add_argument('cache_dir', help='Destination directory for thumbnails')
    parser.add_argument('--max_dim', type=int, default=128,
                       help='Maximum dimension for thumbnails (default: 128)')
    
    args = parser.parse_args()
    
    try:
        success, errors = generate_thumbnails(
            args.input_dir,
            args.cache_dir,
            args.max_dim
        )
        
        if errors > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()