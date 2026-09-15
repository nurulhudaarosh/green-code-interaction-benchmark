from PIL import Image


def compute_ahash(image_path, hash_size=8):
    """
    Compute the classic average hash (aHash) of an image.

    Parameters:
        image_path (str): Path to the input image.
        hash_size (int): Size of the square hash grid.

    Returns:
        str: Binary hash string of length hash_size * hash_size.
    """
    if not isinstance(hash_size, int) or hash_size <= 0:
        raise ValueError("hash_size must be a positive integer")

    with Image.open(image_path) as img:
        # Convert the image to grayscale
        grayscale = img.convert("L")

        # Resize to hash_size x hash_size
        resized = grayscale.resize(
            (hash_size, hash_size),
            Image.Resampling.LANCZOS
        )

        # Get grayscale pixel values
        pixels = list(resized.getdata())

        # Calculate the TRUE mean of the resized pixels
        mean = sum(pixels) / len(pixels)

        # Compare each pixel to the actual mean.
        # Using >= consistently breaks ties in favor of 1.
        #
        # For a fully uniform image:
        #     pixel == mean for every pixel
        # so the result is an all-1s hash.
        hash_bits = [
            "1" if pixel >= mean else "0"
            for pixel in pixels
        ]

        return "".join(hash_bits)


def hamming_distance(hash_a, hash_b):
    """
    Calculate the Hamming distance between two binary hashes.

    Parameters:
        hash_a (str): First binary hash.
        hash_b (str): Second binary hash.

    Returns:
        int: Number of differing bits.
    """
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must have the same length")

    if any(bit not in "01" for bit in hash_a + hash_b):
        raise ValueError("Hashes must contain only '0' and '1'")

    return sum(
        bit_a != bit_b
        for bit_a, bit_b in zip(hash_a, hash_b)
    )


def find_similar_pairs(image_paths, threshold):
    """
    Find all unique pairs of images whose Hamming distance
    is less than or equal to the given threshold.

    Parameters:
        image_paths (list): List of image file paths.
        threshold (int): Maximum allowed Hamming distance.

    Returns:
        list: List of tuples:
              (image_path_a, image_path_b, distance)
    """
    if not isinstance(threshold, int) or threshold < 0:
        raise ValueError("threshold must be a non-negative integer")

    # Compute each hash only once
    hashes = {
        image_path: compute_ahash(image_path)
        for image_path in image_paths
    }

    similar_pairs = []

    paths = list(hashes.keys())

    # Compare every unique pair
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            path_a = paths[i]
            path_b = paths[j]

            distance = hamming_distance(
                hashes[path_a],
                hashes[path_b]
            )

            if distance <= threshold:
                similar_pairs.append(
                    (path_a, path_b, distance)
                )

    return similar_pairs


# Example usage
if __name__ == "__main__":
    image_paths = [
        "image1.jpg",
        "image2.jpg",
        "image3.jpg",
        "image4.jpg"
    ]

    threshold = 5

    similar_pairs = find_similar_pairs(
        image_paths,
        threshold
    )

    for image_a, image_b, distance in similar_pairs:
        print(
            f"{image_a} <-> {image_b}: "
            f"Hamming distance = {distance}"
        )