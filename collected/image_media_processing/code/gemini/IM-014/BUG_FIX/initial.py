import os
from pathlib import Path
from PIL import Image

def bulk_reencode(input_dir: str | Path, output_dir: str | Path, quality: int = 85) -> list[dict]:
    """
    Re-encodes all valid images in input_dir as JPEGs at the specified quality setting.
    
    Parameters:
        input_dir: Directory containing source images.
        output_dir: Target directory where JPEG files will be saved.
        quality: JPEG compression quality (1-95, higher means better quality/larger size).
        
    Returns:
        A list of dictionaries with original size, new size, and compression ratio per file.
    """
    in_path = Path(input_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Common image extensions to process
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    for file_path in in_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            try:
                original_size = file_path.stat().st_size
                
                # Output filename with .jpg extension
                output_file_path = out_path / f"{file_path.stem}.jpg"
                
                with Image.open(file_path) as img:
                    # Convert transparent or paletted images to RGB prior to saving as JPEG
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")
                    
                    # Save as JPEG with specified quality
                    img.save(output_file_path, "JPEG", quality=quality, optimize=True)
                
                reencoded_size = output_file_path.stat().st_size
                
                # Calculate compression ratio (original_size / reencoded_size)
                # Ratio > 1.0 indicates space saved; < 1.0 means re-encoded file is larger
                ratio = original_size / reencoded_size if reencoded_size > 0 else 0.0
                savings_pct = ((original_size - reencoded_size) / original_size) * 100 if original_size > 0 else 0.0
                
                stats = {
                    "filename": file_path.name,
                    "output_filename": output_file_path.name,
                    "original_size_bytes": original_size,
                    "reencoded_size_bytes": reencoded_size,
                    "ratio": round(ratio, 2),
                    "savings_percent": round(savings_pct, 2)
                }
                results.append(stats)
                
                print(f"[{file_path.name}] -> [{output_file_path.name}] | "
                      f"Original: {original_size / 1024:.2f} KB | "
                      f"New: {reencoded_size / 1024:.2f} KB | "
                      f"Ratio: {ratio:.2f}x ({savings_pct:+.1f}%)")
                
            except Exception as e:
                print(f"Skipping {file_path.name}: {e}")

    return results

# Example Usage:
if __name__ == "__main__":
    # Process images from 'source_images' directory and output to 'compressed_jpegs' with 80% quality
    report = bulk_reencode("source_images", "compressed_jpegs", quality=80)