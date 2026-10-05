import os
from pathlib import Path
from PIL import Image

def bulk_reencode(input_dir: str | Path, output_dir: str | Path, quality: int = 85) -> list[dict]:
    """
    Re-encodes all valid images in input_dir as JPEGs at the specified quality setting.
    Handles RGBA, Palette ('P'), grayscale, CMYK, and transparent images safely.
    """
    in_path = Path(input_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    results = []
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    for file_path in in_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            try:
                original_size = file_path.stat().st_size
                output_file_path = out_path / f"{file_path.stem}.jpg"
                
                with Image.open(file_path) as img:
                    # Convert any non-RGB mode (RGBA, P, LA, CMYK, L, etc.) to RGB
                    if img.mode != "RGB":
                        # If image has alpha/transparency, composite onto a white background
                        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                            # Convert to RGBA first to get clean alpha mask
                            rgba_img = img.convert("RGBA")
                            background = Image.new("RGB", rgba_img.size, (255, 255, 255))
                            background.paste(rgba_img, mask=rgba_img.split()[3])
                            img = background
                        else:
                            # Direct conversion for palette, grayscale, CMYK, etc.
                            img = img.convert("RGB")
                    
                    # Save cleanly as JPEG
                    img.save(output_file_path, "JPEG", quality=quality, optimize=True)
                
                reencoded_size = output_file_path.stat().st_size
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