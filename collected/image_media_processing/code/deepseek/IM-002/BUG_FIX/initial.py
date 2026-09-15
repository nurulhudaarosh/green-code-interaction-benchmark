#!/usr/bin/env python3
"""
Thumbnail Generator - Recursively creates aspect-ratio-preserving thumbnails
"""

import os
import sys
from pathlib import Path
from PIL import Image


def generate_thumbnails(input_dir, cache_dir, max_dim=128):
    """Generate thumbnails mirroring input directory structure."""
    input_path = Path(input_dir)
    cache_path = Path(cache_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' not found")
    
    IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    created = skipped = errors = 0
    
    for root, dirs, files in os.walk(input_path):
        rel_path = Path(root).relative_to(input_path)
        target_dir = cache_path / rel_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for filename in files:
            file_path = Path(root) / filename
            
            if file_path.suffix.lower() not in IMAGE_EXTS:
                skipped += 1
                continue
            
            thumb_path = target_dir / filename
            
            # Skip if thumbnail is up-to-date
            if thumb_path.exists() and thumb_path.stat().st_mtime >= file_path.stat().st_mtime:
                skipped += 1
                continue
            
            try:
                _create_thumbnail(file_path, thumb_path, max_dim)
                created += 1
            except Exception as e:
                print(f"⚠ Error: {file_path.relative_to(input_path)} -> {e}", file=sys.stderr)
                errors += 1
    
    return created, skipped, errors


def _create_thumbnail(src, dst, max_dim):
    """Create a single thumbnail preserving aspect ratio."""
    with Image.open(src) as img:
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode == 'RGBA':
                bg.paste(img, mask=img.split()[-1])
            else:
                bg.paste(img)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize preserving aspect ratio
        width, height = img.size
        scale = min(max_dim / width, max_dim / height)
        if scale < 1:  # Only shrink, don't enlarge
            new_size = (int(width * scale), int(height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        img.save(dst, 'JPEG', quality=85, optimize=True)


def main():
    """Command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate aspect-ratio-preserving thumbnails mirroring directory structure'
    )
    parser.add_argument('input_dir', help='Source directory')
    parser.add_argument('cache_dir', help='Destination directory')
    parser.add_argument('--max-dim', type=int, default=128,
                       help='Maximum dimension (default: 128)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress output')
    
    args = parser.parse_args()
    
    try:
        created, skipped, errors = generate_thumbnails(
            args.input_dir,
            args.cache_dir,
            args.max_dim
        )
        
        if not args.quiet:
            print(f"\n✅ Created: {created}")
            print(f"⏭ Skipped: {skipped}")
            print(f"❌ Errors:  {errors}")
            print(f"📁 Cache:   {args.cache_dir}")
        
        sys.exit(1 if errors > 0 else 0)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()