from pathlib import Path

from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """Resize every image in input_dir to exactly target_size (width, height).

    Aspect ratio is preserved: the image is scaled to fit inside the target,
    then centered on a canvas filled with pad_color. Results are written to
    output_dir with the same file names. Returns the number of images saved.
    """
    target_w, target_h = target_size
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue

        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")  # respect EXIF rotation
            w, h = img.size

            scale = min(target_w / w, target_h / h)
            new_w = min(target_w, max(1, round(w * scale)))
            new_h = min(target_h, max(1, round(h * scale)))
            resized = img.resize((new_w, new_h), Image.LANCZOS)

            canvas = Image.new("RGB", (target_w, target_h), pad_color)
            canvas.paste(resized, ((target_w - new_w) // 2, (target_h - new_h) // 2))
            canvas.save(output_dir / path.name)
            count += 1

    return count


if __name__ == "__main__":
    n = letterbox_resize("images_in", "images_out", (640, 640), pad_color=(114, 114, 114))
    print(f"Processed {n} images")