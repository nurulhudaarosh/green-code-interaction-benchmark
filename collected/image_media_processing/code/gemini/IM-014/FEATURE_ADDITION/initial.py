from pathlib import Path
from PIL import Image

def bulk_reencode(input_dir: str | Path, output_dir: str | Path, quality: int = 85) -> list[dict]:
    """
    Re-encodes all images in input_dir to JPEG at specified quality into output_dir.
    Reports original size, re-encoded size, and compression ratio per file.
    
    :param input_dir: Path to the source directory containing images.
    :param output_dir: Path to the directory where re-encoded JPEGs will be saved.
    :param quality: JPEG quality setting (1 to 95; default 85).
    :return: List of dictionaries containing metrics for each processed file.
    """
    in_path = Path(input_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    supported_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".gif"}
    results = []

    total_orig_size = 0
    total_new_size = 0

    print(f"{'Filename':<35} | {'Original':<10} | {'New Size':<10} | {'Ratio':<8} | {'Savings'}")
    print("-" * 80)

    for file_path in in_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            orig_size = file_path.stat().st_size
            dest_file = out_path / f"{file_path.stem}.jpg"

            try:
                with Image.open(file_path) as img:
                    # JPEG does not support transparency (RGBA/P modes); convert to RGB
                    if img.mode in ("RGBA", "P", "LA"):
                        img = img.convert("RGB")
                    
                    # Save as JPEG with specified quality
                    img.save(dest_file, "JPEG", quality=quality, optimize=True)

                new_size = dest_file.stat().st_size
                
                # Compression ratio (Original Size / New Size)
                ratio = orig_size / new_size if new_size > 0 else 0.0
                savings_pct = ((orig_size - new_size) / orig_size) * 100 if orig_size > 0 else 0.0

                record = {
                    "filename": file_path.name,
                    "original_bytes": orig_size,
                    "new_bytes": new_size,
                    "compression_ratio": ratio,
                    "savings_percent": savings_pct
                }
                results.append(record)

                total_orig_size += orig_size
                total_new_size += new_size

                # Format human-readable sizes (KB)
                orig_kb = f"{orig_size / 1024:.1f} KB"
                new_kb = f"{new_size / 1024:.1f} KB"
                
                print(f"{file_path.name:<35} | {orig_kb:<10} | {new_kb:<10} | {ratio:<8.2f}x | {savings_pct:>5.1f}%")

            except Exception as e:
                print(f"Failed to process {file_path.name}: {e}")

    # Display overall aggregate summary
    if results:
        overall_ratio = total_orig_size / total_new_size if total_new_size > 0 else 0.0
        overall_savings = ((total_orig_size - total_new_size) / total_orig_size) * 100 if total_orig_size > 0 else 0.0
        print("-" * 80)
        print(f"TOTAL ({len(results)} files):")
        print(f"Original: {total_orig_size / (1024*1024):.2f} MB | New: {total_new_size / (1024*1024):.2f} MB")
        print(f"Overall Ratio: {overall_ratio:.2f}x | Space Saved: {overall_savings:.1f}%")

    return results