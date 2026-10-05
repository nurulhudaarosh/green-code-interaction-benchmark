from PIL import Image
import os


def bulk_reencode(input_dir, output_dir, quality):
    os.makedirs(output_dir, exist_ok=True)

    results = []

    valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(valid_extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        output_name = os.path.splitext(filename)[0] + ".jpg"
        output_path = os.path.join(output_dir, output_name)

        try:
            original_size = os.path.getsize(input_path)

            with Image.open(input_path) as img:
                # JPEG does not support P or RGBA modes.
                img = img.convert("RGB")
                img.save(output_path, "JPEG", quality=quality)

            reencoded_size = os.path.getsize(output_path)

            compression_ratio = (
                original_size / reencoded_size
                if reencoded_size > 0
                else float("inf")
            )

            results.append({
                "file": filename,
                "original_size": original_size,
                "reencoded_size": reencoded_size,
                "compression_ratio": compression_ratio
            })

            print(
                f"{filename}: "
                f"{original_size} -> {reencoded_size} bytes, "
                f"ratio = {compression_ratio:.2f}"
            )

        except Exception as e:
            print(f"Skipping {filename}: {e}")

    return results