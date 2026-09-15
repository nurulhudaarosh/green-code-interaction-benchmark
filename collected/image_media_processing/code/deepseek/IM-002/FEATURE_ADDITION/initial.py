import os
import sys
from PIL import Image
from pathlib import Path

def generate_thumbnails(input_dir, cache_dir, max_dim=128):
    """
    Recursively creates aspect-ratio-preserving thumbnails mirroring the input directory tree.
    
    Args:
        input_dir (str): Path to the source directory containing images
        cache_dir (str): Path where thumbnails will be stored
        max_dim (int): Maximum dimension (width or height) for thumbnails. Default 128.
    
    Returns:
        tuple: (success_count, error_count, skipped_count)
    """
    
    # Convert to Path objects for easier handling
    input_path = Path(input_dir)
    cache_path = Path(cache_dir)
    
    # Supported image formats
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    # Validate input directory
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return (0, 1, 0)
    
    if not input_path.is_dir():
        print(f"Error: '{input_dir}' is not a directory.")
        return (0, 1, 0)
    
    # Create cache directory if it doesn't exist
    cache_path.mkdir(parents=True, exist_ok=True)
    
    # Walk through the input directory
    for root, dirs, files in os.walk(input_dir):
        # Calculate relative path from input directory
        rel_path = Path(root).relative_to(input_path)
        target_dir = cache_path / rel_path
        
        # Create corresponding directory in cache
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for filename in files:
            # Check if it's an image file
            file_ext = Path(filename).suffix.lower()
            if file_ext not in IMAGE_EXTENSIONS:
                continue
            
            # Full paths
            source_file = Path(root) / filename
            target_file = target_dir / filename
            
            # Check if thumbnail already exists and is up-to-date
            if target_file.exists():
                # Compare modification times
                source_mtime = source_file.stat().st_mtime
                target_mtime = target_file.stat().st_mtime
                
                # If thumbnail exists and is newer or equal, skip
                if target_mtime >= source_mtime:
                    skipped_count += 1
                    continue
            
            try:
                # Open the image
                with Image.open(source_file) as img:
                    # Get original dimensions
                    orig_width, orig_height = img.size
                    
                    # Calculate new dimensions while preserving aspect ratio
                    if orig_width > orig_height:
                        # Landscape or square
                        new_width = max_dim
                        new_height = int(orig_height * (max_dim / orig_width))
                    else:
                        # Portrait
                        new_height = max_dim
                        new_width = int(orig_width * (max_dim / orig_height))
                    
                    # Ensure we don't upscale (optional: only create thumbnails smaller than original)
                    # Uncomment the following lines if you don't want to upscale small images
                    # new_width = min(new_width, orig_width)
                    # new_height = min(new_height, orig_height)
                    
                    # Resize with high-quality resampling
                    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Save the thumbnail
                    # Preserve original format or convert to JPEG for better compatibility
                    if file_ext in {'.jpg', '.jpeg'}:
                        # Save JPEG with quality optimization
                        img_resized.save(target_file, 'JPEG', quality=85, optimize=True)
                    elif file_ext == '.png':
                        # Save PNG
                        img_resized.save(target_file, 'PNG', optimize=True)
                    elif file_ext == '.gif':
                        # Save GIF (only first frame if animated)
                        img_resized.save(target_file, 'GIF', optimize=True)
                    elif file_ext in {'.tiff', '.tif'}:
                        # Save TIFF
                        img_resized.save(target_file, 'TIFF', compression='tiff_lzw')
                    else:
                        # For other formats, save as JPEG
                        # Convert to RGB if necessary
                        if img_resized.mode in ('RGBA', 'LA', 'P'):
                            rgb_img = img_resized.convert('RGB')
                            rgb_img.save(target_file, 'JPEG', quality=85, optimize=True)
                        else:
                            img_resized.save(target_file, 'JPEG', quality=85, optimize=True)
                    
                    success_count += 1
                    
                    # Optional: Print progress for large directories
                    if success_count % 100 == 0:
                        print(f"Processed {success_count} images...")
                
            except Exception as e:
                print(f"Error processing '{source_file}': {str(e)}")
                error_count += 1
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Successfully created: {success_count} thumbnails")
    print(f"  Errors encountered: {error_count}")
    print(f"  Skipped (already up-to-date): {skipped_count}")
    
    return (success_count, error_count, skipped_count)


# Example usage and test function
def test_generate_thumbnails():
    """Test function to demonstrate usage"""
    import tempfile
    import shutil
    
    # Create a test directory with some sample images
    test_input = tempfile.mkdtemp(prefix="test_input_")
    test_cache = tempfile.mkdtemp(prefix="test_cache_")
    
    # Create sample directory structure
    subdir = Path(test_input) / "subfolder"
    subdir.mkdir()
    
    # Note: You'd need actual image files for testing
    # This is just a demonstration of the directory structure
    
    print(f"Test input directory: {test_input}")
    print(f"Test cache directory: {test_cache}")
    
    # Generate thumbnails
    success, errors, skipped = generate_thumbnails(test_input, test_cache, max_dim=128)
    
    # Clean up
    shutil.rmtree(test_input)
    shutil.rmtree(test_cache)
    
    return success, errors, skipped


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) >= 3:
        input_dir = sys.argv[1]
        cache_dir = sys.argv[2]
        max_dim = int(sys.argv[3]) if len(sys.argv) > 3 else 128
        
        generate_thumbnails(input_dir, cache_dir, max_dim)
    else:
        print("Usage: python script.py <input_directory> <cache_directory> [max_dimension]")
        print("Example: python script.py ./photos ./thumbnails 150")
        print("\nRunning test...")
        test_generate_thumbnails()