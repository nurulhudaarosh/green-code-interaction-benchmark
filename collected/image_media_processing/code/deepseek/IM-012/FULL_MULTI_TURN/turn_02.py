import os
from pathlib import Path
from PIL import Image

def letterbox_resize(input_dir, output_dir, target_size, pad_color=(0, 0, 0)):
    """
    Resize all images in input_dir preserving aspect ratio, padding to target_size.
    Content is centered; padding uses pad_color.

    Scale factor = min(target_w / src_w, target_h / src_h)  <-- guarantees fit.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_w, target_h = target_size
    if target_w <= 0 or target_h <= 0:
        raise ValueError("target_size must be positive (width, height)")

    valid_ext = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff', '.gif'}

    for img_path in input_dir.iterdir():
        if not img_path.is_file() or img_path.suffix.lower() not in valid_ext:
            continue

        try:
            with Image.open(img_path) as img:
                # Normalize mode
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                src_w, src_h = img.size
                if src_w == 0 or src_h == 0:
                    print(f"Skipping {img_path}: zero-sized image")
                    continue

                # --- The fix: scale must respect BOTH dimensions ---
                scale = min(target_w / src_w, target_h / src_h)

                new_w = max(1, int(round(src_w * scale)))
                new_h = max(1, int(round(src_h * scale)))

                # Hard guarantee: never exceed target (guards against rounding)
                new_w = min(new_w, target_w)
                new_h = min(new_h, target_h)

                resized = img.resize((new_w, new_h), Image.LANCZOS)

                # Build canvas
                if resized.mode == 'L':
                    if isinstance(pad_color, (tuple, list)):
                        pad_val = pad_color[0] if len(pad_color) == 1 else sum(pad_color) // 3
                    else:
                        pad_val = pad_color
                    canvas = Image.new('L', (target_w, target_h), pad_val)
                else:
                    canvas = Image.new('RGB', (target_w, target_h), pad_color)

                # Center the resized content
                paste_x = (target_w - new_w) // 2
                paste_y = (target_h - new_h) // 2
                canvas.paste(resized, (paste_x, paste_y))

                out_path = output_dir / img_path.name
                save_kwargs = {}
                if out_path.suffix.lower() in ('.jpg', '.jpeg'):
                    save_kwargs['quality'] = 95
                    save_kwargs['subsampling'] = 0
                canvas.save(out_path, **save_kwargs)

        except Exception as e:
            print(f"Failed to process {img_path}: {e}")

    print(f"Done. Processed images saved to {output_dir}")