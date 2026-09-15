import os
import sys
from PIL import Image
from pathlib import Path

def generate_thumbnails(input_dir, cache_dir, max_dim=128, extensions=None):
    """
    Recursively creates aspect-ratio-preserving thumbnails mirroring the input directory tree.
    
    Args:
        input_dir (str): Path to the source directory containing images
        cache_dir (str): Path where thumbnails will be stored
        max_dim (int): Maximum dimension (width or height) for thumbnails. Default 128.
        extensions (list): List of file extensions to include (e.g., ['.png', '.jpg', '.jpeg']).
                          Defaults to ['.png', '.jpg', '.jpeg'].
    
    Returns:
        tuple: (success_count, error_count, skipped_count, unsupported_count)
    """
    
    # Convert to Path objects for easier handling
    input_path = Path(input_dir)
    cache_path = Path(cache_dir)
    
    # Set default extensions if not provided
    if extensions is None:
        extensions = ['.png', '.jpg', '.jpeg']
    else:
        # Normalize extensions to lowercase with dot prefix
        normalized_extensions = []
        for ext in extensions:
            ext = ext.lower().strip()
            if not ext.startswith('.'):
                ext = '.' + ext
            normalized_extensions.append(ext)
        extensions = normalized_extensions
    
    # All supported extensions by PIL
    ALL_SUPPORTED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
        '.ico', '.ppm', '.pgm', '.pbm', '.xbm', '.xpm'
    }
    
    # Filter to only include extensions that are actually supported
    supported_extensions = set(ext for ext in extensions if ext in ALL_SUPPORTED_EXTENSIONS)
    unsupported_extensions = set(ext for ext in extensions if ext not in ALL_SUPPORTED_EXTENSIONS)
    
    # Warn about unsupported extensions
    if unsupported_extensions:
        print(f"Warning: The following extensions are not supported by PIL and will be skipped: {', '.join(unsupported_extensions)}")
    
    # If no supported extensions remain, return early
    if not supported_extensions:
        print("Error: No supported extensions provided. Please check your extension list.")
        return (0, 0, 0, len(unsupported_extensions))
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    unsupported_count = len(unsupported_extensions)
    
    # Validate input directory
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return (0, 1, 0, unsupported_count)
    
    if not input_path.is_dir():
        print(f"Error: '{input_dir}' is not a directory.")
        return (0, 1, 0, unsupported_count)
    
    # Create cache directory if it doesn't exist
    cache_path.mkdir(parents=True, exist_ok=True)
    
    # Print configuration
    print(f"Processing images with extensions: {', '.join(sorted(supported_extensions))}")
    print(f"Maximum dimension: {max_dim}px")
    print(f"Input: {input_path}")
    print(f"Cache: {cache_path}")
    print("-" * 60)
    
    # Walk through the input directory
    for root, dirs, files in os.walk(input_dir):
        # Calculate relative path from input directory
        rel_path = Path(root).relative_to(input_path)
        target_dir = cache_path / rel_path
        
        # Create corresponding directory in cache
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for filename in files:
            # Check if it's an image file with supported extension
            file_ext = Path(filename).suffix.lower()
            
            # Skip if extension not in our supported list
            if file_ext not in supported_extensions:
                # Check if it's in the unsupported list for counting
                if file_ext in unsupported_extensions:
                    unsupported_count += 1
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
                    
                    # Determine output format and save
                    output_format = None
                    save_kwargs = {}
                    
                    if file_ext in {'.jpg', '.jpeg'}:
                        output_format = 'JPEG'
                        save_kwargs = {'quality': 85, 'optimize': True}
                    elif file_ext == '.png':
                        output_format = 'PNG'
                        save_kwargs = {'optimize': True}
                    elif file_ext == '.gif':
                        output_format = 'GIF'
                        save_kwargs = {'optimize': True}
                    elif file_ext in {'.tiff', '.tif'}:
                        output_format = 'TIFF'
                        save_kwargs = {'compression': 'tiff_lzw'}
                    elif file_ext == '.webp':
                        output_format = 'WEBP'
                        save_kwargs = {'quality': 85, 'method': 6}
                    elif file_ext in {'.bmp', '.ppm', '.pgm', '.pbm'}:
                        # These formats don't need special conversion
                        output_format = file_ext[1:].upper()  # Remove dot and uppercase
                    else:
                        # For other supported formats, save as original format
                        output_format = file_ext[1:].upper()
                    
                    # Handle special cases for formats that need RGB conversion
                    if output_format in {'JPEG', 'WEBP'} and img_resized.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = img_resized.convert('RGB')
                        rgb_img.save(target_file, output_format, **save_kwargs)
                    else:
                        img_resized.save(target_file, output_format, **save_kwargs)
                    
                    success_count += 1
                    
                    # Optional: Print progress for large directories
                    if success_count % 100 == 0:
                        print(f"Processed {success_count} images...")
                
            except Exception as e:
                print(f"Error processing '{source_file}': {str(e)}")
                error_count += 1
    
    # Print summary
    print("-" * 60)
    print(f"Summary:")
    print(f"  Successfully created: {success_count} thumbnails")
    print(f"  Errors encountered: {error_count}")
    print(f"  Skipped (already up-to-date): {skipped_count}")
    print(f"  Skipped (unsupported extension): {unsupported_count}")
    
    return (success_count, error_count, skipped_count, unsupported_count)


# Additional utility function for better extension handling
def get_image_extensions():
    """
    Returns a set of all image extensions supported by PIL.
    
    Returns:
        set: Set of supported image extensions
    """
    from PIL import Image
    return set(Image.registered_extensions().keys())


# Extended example with filtering
def example_usage_with_filters():
    """
    Demonstrates various ways to use the extensions parameter
    """
    # Example 1: Default extensions (.png, .jpg, .jpeg)
    print("Example 1: Default extensions")
    generate_thumbnails("./photos", "./thumbnails")
    
    # Example 2: Only PNG files
    print("\nExample 2: Only PNG files")
    generate_thumbnails("./photos", "./thumbnails_png", extensions=['.png'])
    
    # Example 3: Multiple formats with and without dots
    print("\nExample 3: Multiple formats")
    generate_thumbnails("./photos", "./thumbnails_selected", 
                       extensions=['.jpg', '.jpeg', '.png', '.webp'])
    
    # Example 4: Using extension strings without dots
    print("\nExample 4: Extensions without dots")
    generate_thumbnails("./photos", "./thumbnails_webp", 
                       extensions=['webp'])
    
    # Example 5: Mixed extensions (some unsupported)
    print("\nExample 5: Mixed supported and unsupported extensions")
    generate_thumbnails("./photos", "./thumbnails_mixed", 
                       extensions=['.jpg', '.png', '.heic', '.raw'])


if __name__ == "__main__":
    # Command line interface with extensions support
    if len(sys.argv) >= 3:
        input_dir = sys.argv[1]
        cache_dir = sys.argv[2]
        max_dim = int(sys.argv[3]) if len(sys.argv) > 3 else 128
        
        # Parse extensions from command line
        extensions = None
        if len(sys.argv) > 4:
            # Extensions can be passed as a comma-separated list
            # e.g., python script.py ./photos ./thumbnails 150 .png,.jpg,.webp
            ext_str = sys.argv[4]
            extensions = [ext.strip() for ext in ext_str.split(',')]
        
        generate_thumbnails(input_dir, cache_dir, max_dim, extensions)
    else:
        print("Usage: python script.py <input_directory> <cache_directory> [max_dimension] [extensions]")
        print("Example: python script.py ./photos ./thumbnails 150 .png,.jpg,.jpeg")
        print("Example: python script.py ./photos ./thumbnails 128 .png")
        print("\nIf extensions are not specified, defaults to: .png, .jpg, .jpeg")
        print("\nRunning test...")
        example_usage_with_filters()