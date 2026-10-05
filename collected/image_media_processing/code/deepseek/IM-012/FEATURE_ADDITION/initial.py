import os
from pathlib import Path
from PIL import Image


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """
    Resize all images in input_dir to fit within target_size while preserving
    aspect ratio, then pad to exactly target_size with content centered.

    Args:
        input_dir (str | Path): Directory containing source images.
        output_dir (str | Path): Directory to write resized images to.
        target_size (tuple): (width, height) of the output image.
        pad_color (tuple): RGB color tuple for padding. Default black.

    Returns:
        list[Path]: Paths of successfully written output images.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_w, target_h = target_size
    if target_w <= 0 or target_h <= 0:
        raise ValueError("target_size dimensions must be positive")

    # Ensure pad_color has the right number of components for the mode
    supported_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    written = []

    for src_path in sorted(input_dir.iterdir()):
        if not src_path.is_file() or src_path.suffix.lower() not in supported_exts:
            continue

        try:
            with Image.open(src_path) as img:
                orig_w, orig_h = img.size
                if orig_w == 0 or orig_h == 0:
                    continue

                # Scale factor to fit inside target box
                scale = min(target_w / orig_w, target_h / orig_h)
                new_w = max(1, int(round(orig_w * scale)))
                new_h = max(1, int(round(orig_h * scale)))

                # High-quality downscale / upscale
                resample = Image.LANCZOS if scale < 1 else Image.BICUBIC
                resized = img.resize((new_w, new_h), resample)

                # Build a fresh canvas in a mode matching the source (RGB/RGBA)
                mode = resized.mode
                if mode == "RGBA":
                    bg_color = tuple(pad_color) + (255,) if len(pad_color) == 3 else tuple(pad_color)
                elif mode == "L":
                    # grayscale padding uses luminance approximation
                    bg_color = int(0.299 * pad_color[0] + 0.587 * pad_color[1] + 0.114 * pad_color[2])
                else:
                    bg_color = tuple(pad_color[:3])

                canvas = Image.new(mode, (target_w, target_h), bg_color)

                # Center the resized image
                offset_x = (target_w - new_w) // 2
                offset_y = (target_h - new_h) // 2

                if mode == "RGBA":
                    canvas.paste(resized, (offset_x, offset_y), resized)
                else:
                    canvas.paste(resized, (offset_x, offset_y))

                # Save preserving format; force RGB for JPEG (no alpha)
                out_path = output_dir / src_path.name
                save_img = canvas
                save_kwargs = {}
                suffix = src_path.suffix.lower()
                if suffix in {".jpg", ".jpeg"}:
                    if save_img.mode != "RGB":
                        save_img = save_img.convert("RGB")
                    save_kwargs = {"quality": 95, "subsampling": 0}
                elif suffix == ".png":
                    save_kwargs = {"optimize": True}

                save_img.save(out_path, **save_kwargs)
                written.append(out_path)

        except (OSError, ValueError) as e:
            print(f"Skipping {src_path.name}: {e}")

    return written


if __name__ == "__main__":
    letterbox_resize("input_images", "output_images", (640, 640), pad_color=(0, 0, 0))