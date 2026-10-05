import os
from PIL import Image
import numpy as np


def find_near_duplicates(input_dir, threshold):
    """
    Cluster images using normalized grayscale histogram L1 distance.

    Two images are connected when their histogram L1 distance is
    <= threshold. Union-find then resolves these connections
    transitively, so A-B-C form one cluster even if A-C exceeds
    the threshold.

    Returns:
        list[list[str]]: Clusters of image paths.
    """
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    extensions = {
        ".jpg", ".jpeg", ".png", ".bmp",
        ".tif", ".tiff", ".webp"
    }

    image_paths = sorted(
        os.path.join(input_dir, name)
        for name in os.listdir(input_dir)
        if os.path.splitext(name)[1].lower() in extensions
    )

    n = len(image_paths)

    # -------------------------
    # Union-Find
    # -------------------------
    parent = list(range(n))
    rank = [0] * n

    def find(x):
        # Path compression
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a, b):
        # Union by rank
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return

        if rank[root_a] < rank[root_b]:
            root_a, root_b = root_b, root_a

        parent[root_b] = root_a

        if rank[root_a] == rank[root_b]:
            rank[root_a] += 1

    # -------------------------
    # Compute normalized histograms
    # -------------------------
    histograms = []

    for path in image_paths:
        with Image.open(path) as img:
            gray = np.asarray(img.convert("L"), dtype=np.uint8)

        hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)

        # Normalize histogram so its sum is 1
        total = hist.sum()
        if total > 0:
            hist /= total

        histograms.append(hist)

    # -------------------------
    # Build connectivity graph
    # -------------------------
    # IMPORTANT:
    # We union every pair that satisfies the threshold.
    # Union-find preserves transitive connectivity.
    #
    # Example:
    #   distance(A, B) <= threshold  -> union(A, B)
    #   distance(B, C) <= threshold  -> union(B, C)
    #
    # Even if:
    #   distance(A, C) > threshold
    #
    # A, B, and C still have the same root.
    # -------------------------
    for i in range(n):
        for j in range(i + 1, n):
            distance = np.abs(histograms[i] - histograms[j]).sum()

            if distance <= threshold:
                union(i, j)

    # -------------------------
    # Collect connected components
    # -------------------------
    clusters = {}

    for i, path in enumerate(image_paths):
        root = find(i)
        clusters.setdefault(root, []).append(path)

    return list(clusters.values())