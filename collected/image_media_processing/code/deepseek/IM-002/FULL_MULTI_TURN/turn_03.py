import os
import sys
from PIL import Image
from pathlib import Path

def generate_thumbnails(input_dir, cache_dir, max_dim=128, extensions=None):
    """
    Recursively creates aspect-ratio-preserving thumbnails mirroring the input directory tree.
    
    Args:
        input_dir (str): Path to the source directory containing images
        cache_dir (str): Path to the destination directory for thumbnails
        max_dim (int): Maximum dimension (width or height) for thumbnails. Defaults to 128.
        extensions (list): List of file extensions to include (e.g., ['.jpg', '.png']). 
                          Defaults to ['.png', '.jpg', '.jpeg'].
    
    Returns:
        tuple: (success_count, skip_count, error_count, skipped_extensions_count)
    """
    
    # Convert to Path objects for easier handling
    input_path = Path(input_dir)
    cache_path = Path(cache_dir)
    
    # Set default extensions if none provided
    if extensions is None:
        extensions = ['.png', '.jpg', '.jpeg']
    else:
        # Normalize extensions: ensure they start with a dot and are lowercase
        extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                     for ext in extensions]
    
    # Convert to set for faster lookup
    allowed_extensions = set(extensions)
    
    # Statistics
    success_count = 0
    skip_count = 0
    error_count = 0
    skipped_extensions_count = 0
    
    # Walk through the input directory recursively
    for root, dirs, files in os.walk(input_path):
        # Compute the relative path from input_dir
        rel_path = Path(root).relative_to(input_path)
        
        # Create corresponding directory in cache
        target_dir = cache_path / rel_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each file in the current directory
        for filename in files:
            file_path = Path(root) / filename
            file_ext = file_path.suffix.lower()
            
            # Skip files with extensions not in the allowed list
            if file_ext not in allowed_extensions:
                skipped_extensions_count += 1
                continue
            
            # Construct target thumbnail path (preserve original filename)
            thumbnail_path = target_dir / filename
            
            # Skip if thumbnail already exists and is newer than source
            if thumbnail_path.exists():
                try:
                    source_mtime = file_path.stat().st_mtime
                    thumb_mtime = thumbnail_path.stat().st_mtime
                    if thumb_mtime >= source_mtime:
                        skip_count += 1
                        continue
                except (OSError, FileNotFoundError):
                    # If we can't stat, just regenerate
                    pass
            
            # Generate thumbnail
            try:
                with Image.open(file_path) as img:
                    # Make a copy to avoid modifying the original
                    img_copy = img.copy()
                    
                    # Use thumbnail() which preserves aspect ratio
                    # It resizes so that both dimensions are <= max_dim
                    img_copy.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                    
                    # Handle color mode conversion for different formats
                    if file_ext in {'.jpg', '.jpeg'}:
                        # JPEG doesn't support alpha
                        if img_copy.mode in ('RGBA', 'LA', 'P'):
                            img_copy = img_copy.convert('RGB')
                    elif file_ext in {'.png', '.gif'}:
                        # Preserve transparency for PNG/GIF
                        if img_copy.mode == 'P':
                            # Palette mode might have transparency
                            img_copy = img_copy.convert('RGBA')
                        # RGBA/LA are fine as-is
                    
                    # Determine save format and options
                    save_kwargs = {}
                    if file_ext in {'.jpg', '.jpeg'}:
                        save_kwargs['quality'] = 85
                        save_kwargs['optimize'] = True
                    elif file_ext == '.png':
                        save_kwargs['optimize'] = True
                    elif file_ext == '.gif':
                        save_kwargs['optimize'] = True
                    
                    # Save thumbnail
                    img_copy.save(thumbnail_path, **save_kwargs)
                    success_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Error processing {file_path}: {e}", file=sys.stderr)
    
    return success_count, skip_count, error_count, skipped_extensions_count


# Example usage and CLI wrapper
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate aspect-ratio-preserving thumbnails recursively"
    )
    parser.add_argument("input_dir", help="Source directory containing images")
    parser.add_argument("cache_dir", help="Destination directory for thumbnails")
    parser.add_argument(
        "--max-dim", 
        type=int, 
        default=128,
        help="Maximum dimension for thumbnails (default: 128)"
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=['.png', '.jpg', '.jpeg'],
        help="File extensions to include (e.g., --extensions .jpg .png .gif). Default: .png .jpg .jpeg"
    )
    
    args = parser.parse_args()
    
    # Validate directories
    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(args.input_dir):
        print(f"Error: '{args.input_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Create cache directory if it doesn't exist
    os.makedirs(args.cache_dir, exist_ok=True)
    
    # Generate thumbnails
    success, skipped, errors, skipped_ext = generate_thumbnails(
        args.input_dir, 
        args.cache_dir, 
        args.max_dim,
        args.extensions
    )
    
    # Print summary
    print(f"Thumbnails generated: {success}")
    print(f"Skipped (up to date): {skipped}")
    print(f"Skipped (unsupported extension): {skipped_ext}")
    print(f"Errors: {errors}")
    
    if errors > 0:
        sys.exit(1)