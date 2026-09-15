from PIL import Image
from itertools import combinations

def compute_ahash(image_path, hash_size=8):
    """
    Compute the average hash (aHash) of an image.

    Steps:
    1. Open image, convert to grayscale.
    2. Resize to (hash_size x hash_size) pixels.
    3. Compute the true mean of the resized pixel values.
    4. Build a bit for each pixel: 1 if pixel >= mean else 0.
       (Ties, e.g. a fully uniform image where every pixel == mean,
       resolve to 1 via ">=", giving a well-defined all-1s hash.)
    5. Pack bits into an integer.

    Returns:
        int: an integer with hash_size*hash_size bits representing the hash.
    """
    img = Image.open(image_path).convert("L")  # grayscale
    img = img.resize((hash_size, hash_size), Image.LANCZOS)

    pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)  # true mean of the resized pixels

    bits = 0
    for pixel in pixels:
        bits <<= 1
        if pixel >= avg:  # ties (pixel == avg) resolve to 1, consistently
            bits |= 1

    return bits


def hamming_distance(hash_a, hash_b):
    """
    Compute the Hamming distance between two integer hashes,
    i.e. the number of differing bits.
    """
    return bin(hash_a ^ hash_b).count("1")


def find_similar_pairs(image_paths, threshold, hash_size=8):
    """
    Find all pairs of images whose average-hash Hamming distance is <= threshold.

    Args:
        image_paths (list[str]): paths to the images to compare.
        threshold (int): maximum Hamming distance for a pair to be considered similar.
        hash_size (int): hash grid size, must match across all compared images.

    Returns:
        list[tuple[str, str, int]]: list of (path_a, path_b, distance) tuples for
            every pair whose distance is <= threshold, sorted by ascending distance.
    """
    hashes = {}
    for path in image_paths:
        try:
            hashes[path] = compute_ahash(path, hash_size=hash_size)
        except Exception as e:
            print(f"Warning: could not process '{path}': {e}")

    valid_paths = list(hashes.keys())

    similar_pairs = []
    for path_a, path_b in combinations(valid_paths, 2):
        dist = hamming_distance(hashes[path_a], hashes[path_b])
        if dist <= threshold:
            similar_pairs.append((path_a, path_b, dist))

    similar_pairs.sort(key=lambda triple: triple[2])
    return similar_pairs


def _test_uniform_image_hash(hash_size=8):
    """
    Self-test: a fully uniform (flat-color) image should hash to all-1 bits
    (2**(hash_size*hash_size) - 1), with no errors or ambiguity, since every
    pixel equals the mean exactly and ties resolve to 1.
    """
    uniform_img = Image.new("L", (hash_size, hash_size), color=127)
    tmp_path = "_uniform_test_image.png"
    uniform_img.save(tmp_path)

    h = compute_ahash(tmp_path, hash_size=hash_size)
    expected = (1 << (hash_size * hash_size)) - 1  # all bits set

    assert h == expected, (
        f"Uniform image hash mismatch: got {h:0{hash_size*hash_size}b}, "
        f"expected {expected:0{hash_size*hash_size}b}"
    )

    import os
    os.remove(tmp_path)
    print("Uniform image edge case: OK (all-1s hash, no errors)")


if __name__ == "__main__":
    import sys

    _test_uniform_image_hash()

    if len(sys.argv) >= 3:
        h1 = compute_ahash(sys.argv[1])
        h2 = compute_ahash(sys.argv[2])
        print(f"Hash 1: {h1:016x}")
        print(f"Hash 2: {h2:016x}")
        print(f"Hamming distance: {hamming_distance(h1, h2)}")

    # Example usage of find_similar_pairs:
    # paths = ["img1.jpg", "img2.jpg", "img3.jpg"]
    # pairs = find_similar_pairs(paths, threshold=5)
    # for a, b, d in pairs:
    #     print(f"{a} <-> {b}: distance {d}")