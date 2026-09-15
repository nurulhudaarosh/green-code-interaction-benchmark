from PIL import Image
import os


def preprocess_images(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    stats = {}

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)

        if not os.path.isfile(input_path):
            continue

        try:
            # Open and convert to grayscale
            img = Image.open(input_path).convert("L")

            # Get original min/max pixel values
            min_val = min(img.getdata())
            max_val = max(img.getdata())

            stats[filename] = {
                "min": min_val,
                "max": max_val
            }

            # Min-max normalization to 0-255
            if max_val != min_val:
                img = img.point(
                    lambda p: int((p - min_val) * 255 / (max_val - min_val))
                )
            else:
                # Handle uniformly colored images
                img = img.point(lambda p: 0)

            # Save as PNG
            output_filename = os.path.splitext(filename)[0] + ".png"
            output_path = os.path.join(output_dir, output_filename)
            img.save(output_path, "PNG")

        except Exception:
            # Skip files that are not valid images
            continue

    return stats