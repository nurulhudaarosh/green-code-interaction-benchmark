import os
from pathlib import Path
from PIL import Image

def bulk_reencode(input_dir: str, output_dir: str, quality: int = 85) -> list[dict]:
    """
    Re-encodes all images in `input_dir` as JPEG to `output_dir` at specified quality.
    
    Args:
        input_dir: Path to source directory containing images.
        output_dir: Path to destination directory.
        quality: JPEG quality setting (1-95, default 85).
        
    Returns:
        List of dictionaries with per-file stats, plus an overall summary dict 
        identified by the key 'rel_path': '__summary__' at the end.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".gif"}
    stats = []

    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in valid_exts:
            rel_path = file_path.relative_to(input_path)
            target_file = output_path / rel_path.with_suffix(".jpg")
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with Image.open(file_path) as img:
                    # Convert any non-RGB image mode to RGB before JPEG save
                    if img.mode != "RGB":
                        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                            rgba_img = img.convert("RGBA")
                            background = Image.new("RGB", rgba_img.size, (255, 255, 255))
                            background.paste(rgba_img, mask=rgba_img.split()[3])
                            img = background
                        else:
                            img = img.convert("RGB")
                    
                    img.save(target_file, "JPEG", quality=quality, optimize=True)
                
                orig_size = file_path.stat().st_size
                new_size = target_file.stat().st_size
                ratio = orig_size / new_size if new_size > 0 else 0.0
                savings_pct = ((orig_size - new_size) / orig_size * 100) if orig_size > 0 else 0.0
                
                file_stat = {
                    "rel_path": str(rel_path),
                    "original_bytes": orig_size,
                    "reencoded_bytes": new_size,
                    "ratio": ratio,
                    "savings_pct": savings_pct,
                }
                stats.append(file_stat)
                
                print(
                    f"Processed: {rel_path}\n"
                    f"  Original:   {orig_size / 1024:.2f} KB\n"
                    f"  Re-encoded: {new_size / 1024:.2f} KB\n"
                    f"  Ratio:      {ratio:.2f}x ({savings_pct:+.1f}% space change)\n"
                )

            except Exception as e:
                print(f"Failed to process {rel_path}: {e}")

    # Compute overall summary
    total_orig = sum(s["original_bytes"] for s in stats)
    total_new = sum(s["reencoded_bytes"] for s in stats)
    total_ratio = total_orig / total_new if total_new > 0 else 0.0
    total_savings_pct = ((total_orig - total_new) / total_orig * 100) if total_orig > 0 else 0.0

    summary = {
        "rel_path": "__summary__",
        "total_files": len(stats),
        "original_bytes": total_orig,
        "reencoded_bytes": total_new,
        "ratio": total_ratio,
        "savings_pct": total_savings_pct,
    }
    
    if stats:
        print("-" * 50)
        print(f"Total files: {summary['total_files']}")
        print(f"Total original size:   {total_orig / (1024 * 1024):.2f} MB")
        print(f"Total reencoded size:  {total_new / (1024 * 1024):.2f} MB")
        print(f"Overall compression:   {total_ratio:.2f}x ({total_savings_pct:+.1f}% overall)")

    stats.append(summary)
    return stats