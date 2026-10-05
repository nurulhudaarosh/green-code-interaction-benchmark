import os
from PIL import Image
import numpy as np


def find_near_duplicates(input_dir, threshold):
    """
    Cluster images by normalized grayscale histogram L1 distance.

    Two images are considered near-duplicates when their histogram
    L1 distance is <= threshold. Union-find is used so that the
    clustering is transitive: if A~B and B~C, all three belong
    to the same cluster.

    Args:
        input_dir (str): Directory containing image files.
        threshold (float): Maximum allowed L1 histogram distance.

    Returns:
        list[list[str]]: Clusters containing image file paths.
    """
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}

    image_paths = sorted(
        os.path.join(input_dir, name)
        for name in os.listdir(input_dir)
        if os.path.splitext(name)[1].lower() in extensions
    )

    if not image_paths:
        return []

    # Compute normalized grayscale histograms.
    histograms = []
    valid_paths = []

    for path in image_paths:
        try:
            with Image.open(path) as img:
                gray = img.convert("L")
                hist = np.histogram(
                    np.asarray(gray),
                    bins=256,
                    range=(0, 256)
                )[0].astype(np.float64)

                total = hist.sum()
                if total > 0:
                    hist /= total

                histograms.append(hist)
                valid_paths.append(path)

        except (OSError, ValueError):
            # Skip files that cannot be opened as images.
            continue

    n = len(valid_paths)

    if n == 0:
        return []

    # Union-find data structure.
    parent = list(range(n))
    rank = [0] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # Path compression
            x = parent[x]
        return x

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return

        # Union by rank.
        if rank[root_a] < rank[root_b]:
            parent[root_a] = root_b
        elif rank[root_a] > rank[root_b]:
            parent[root_b] = root_a
        else:
            parent[root_b] = root_a
            rank[root_a] += 1

    # Compare every pair and union close images.
    for i in range(n):
        for j in range(i + 1, n):
            distance = np.sum(np.abs(histograms[i] - histograms[j]))

            if distance <= threshold:
                union(i, j)

    # Build transitive clusters.
    clusters = {}

    for i, path in enumerate(valid_paths):
        root = find(i)
        clusters.setdefault(root, []).append(path)

    return list(clusters.values())