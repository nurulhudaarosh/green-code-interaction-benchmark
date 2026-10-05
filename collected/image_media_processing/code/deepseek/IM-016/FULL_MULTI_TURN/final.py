import os
import numpy as np
from PIL import Image


# Explicit Sobel kernels.
# Gx: horizontal-gradient kernel (derivative along x / columns).
#     A purely vertical edge (intensity varies left-to-right) gives a strong Gx.
SOBEL_GX = np.array([
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1],
], dtype=np.float32)

# Gy: vertical-gradient kernel (derivative along y / rows).
#     A purely horizontal edge (intensity varies top-to-bottom) gives a strong Gy.
SOBEL_GY = np.array([
    [-1, -2, -1],
    [ 0,  0,  0],
    [ 1,  2,  1],
], dtype=np.float32)


def _convolve2d(image, kernel):
    """Valid 2D convolution of a grayscale image with a 3x3 kernel.

    The caller must guarantee that image has at least kh rows and kw columns.
    """
    kh, kw = kernel.shape
    H, W = image.shape
    assert H >= kh and W >= kw, "image too small for kernel"
    out_h = H - kh + 1
    out_w = W - kw + 1
    out = np.zeros((out_h, out_w), dtype=np.float32)

    for i in range(kh):
        for j in range(kw):
            k = kernel[i, j]
            if k != 0.0:
                out += k * image[i:i + out_h, j:j + out_w]
    return out


def _pad_to_shape(arr, target_shape, mode='edge'):
    """Pad a 2D array symmetrically to match target_shape.

    Uses 'edge' (replicate) by default so border pixels repeat the nearest
    valid value. Any extra row/column from an odd difference is added at the
    bottom/right.
    """
    th, tw = target_shape
    h, w = arr.shape
    pad_top = (th - h) // 2
    pad_bottom = th - h - pad_top
    pad_left = (tw - w) // 2
    pad_right = tw - w - pad_left
    return np.pad(
        arr,
        ((pad_top, pad_bottom), (pad_left, pad_right)),
        mode=mode,
    )


def _sobel_magnitude(gray):
    """Compute the Sobel gradient magnitude of a grayscale float image.

    Handles 1-pixel-wide and 1-pixel-tall (and even 1x1) images by
    edge-replicating the input up to at least 3x3 before the valid
    convolution, then padding the result back to the original size.
    """
    H, W = gray.shape
    kh, kw = SOBEL_GX.shape  # 3, 3

    # Replicate-pad the input so a valid 3x3 convolution is defined.
    pad_h = max(0, kh - H)
    pad_w = max(0, kw - W)
    if pad_h or pad_w:
        padded = np.pad(gray, ((0, pad_h), (0, pad_w)), mode='edge')
    else:
        padded = gray

    gx = _convolve2d(padded, SOBEL_GX)
    gy = _convolve2d(padded, SOBEL_GY)

    mag = np.sqrt(gx * gx + gy * gy)

    # Crop/pad back to the original image shape.
    mag = _pad_to_shape(mag, (H, W), mode='edge')[:H, :W]
    return mag


def sobel_edges(input_dir, output_dir, threshold=None):
    """Apply Sobel edge detection to every image in input_dir and save
    grayscale PNGs in output_dir.

    Parameters
    ----------
    input_dir : str
        Directory containing input images.
    output_dir : str
        Directory where output PNGs are written.
    threshold : float or None, optional
        If None (default), the raw gradient magnitude (clipped to [0, 255])
        is saved. If a number is provided, the magnitude map is binarized:
        pixels whose magnitude is strictly greater than `threshold` become
        255, and all others become 0.
    """
    if threshold is not None:
        threshold = float(threshold)

    os.makedirs(output_dir, exist_ok=True)

    valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp')

    for fname in sorted(os.listdir(input_dir)):
        if not fname.lower().endswith(valid_exts):
            continue

        in_path = os.path.join(input_dir, fname)
        out_name = os.path.splitext(fname)[0] + '.png'
        out_path = os.path.join(output_dir, out_name)

        with Image.open(in_path) as img:
            gray = np.asarray(img.convert('L'), dtype=np.float32)

        mag = _sobel_magnitude(gray)

        if threshold is None:
            out = np.clip(mag, 0, 255).astype(np.uint8)
        else:
            out = np.where(mag > threshold, np.uint8(255), np.uint8(0))

        Image.fromarray(out, mode='L').save(out_path, format='PNG')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Sobel edge detection.")
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument(
        "-t", "--threshold", type=float, default=None,
        help="If set, binarize output (mag > threshold -> 255, else 0)."
    )
    args = parser.parse_args()

    sobel_edges(args.input_dir, args.output_dir, threshold=args.threshold)