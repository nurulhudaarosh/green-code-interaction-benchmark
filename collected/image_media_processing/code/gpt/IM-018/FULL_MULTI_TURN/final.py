id="58321"
import os
from PIL import Image
import numpy as np


def find_near_duplicates(input_dir, threshold, distance_metric="l1"):
    """
    Cluster images by normalized grayscale histogram distance.

    Similarity is transitive:
        A ~ B and B ~ C  =>  A, B, C are in the same cluster.

    Args:
        input_dir (str): Directory containing image files.
        threshold (float): Maximum allowed histogram distance.
        distance_metric (str): "l1" (default) or "chi_squared".

    Returns:
        list[list[str]]: Clusters containing at least two images.

    Raises:
        ValueError: If distance_metric is unsupported.
    """

    if distance_metric not in {"l1", "chi_squared"}:
        raise ValueError(
            "distance_metric must be either 'l1' or 'chi_squared'"
        )

    image_extensions = {
        ".jpg", ".jpeg", ".png", ".bmp",
        ".tif", ".tiff", ".webp"
    }

    image_paths = sorted(
        os.path.join(input_dir, filename)
        for filename in os.listdir(input_dir)
        if os.path.splitext(filename)[1].lower() in image_extensions
    )

    # Zero or one image cannot form a duplicate cluster.
    if len(image_paths) < 2:
        return []

    # Compute normalized grayscale histograms.
    histograms = []

    for path in image_paths:
        with Image.open(path) as img:
            gray = img.convert("L")
            hist = np.asarray(gray.histogram(), dtype=np.float64)

        total = hist.sum()
        if total > 0:
            hist /= total

        histograms.append(hist)

    def histogram_distance(hist_a, hist_b):
        if distance_metric == "l1":
            return np.sum(np.abs(hist_a - hist_b))

        # Chi-squared distance.
        denominator = hist_a + hist_b
        mask = denominator > 0

        return 0.5 * np.sum(
            ((hist_a[mask] - hist_b[mask]) ** 2)
            / denominator[mask]
        )

    # Union-Find.
    parent = list(range(len(image_paths)))
    rank = [0] * len(image_paths)

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return

        if rank[root_a] < rank[root_b]:
            root_a, root_b = root_b, root_a

        parent[root_b] = root_a

        if rank[root_a] == rank[root_b]:
            rank[root_a] += 1

    # Connect every pair within the threshold.
    # Union-Find makes these connections transitive.
    for i in range(len(image_paths)):
        for j in range(i + 1, len(image_paths)):
            distance = histogram_distance(
                histograms[i],
                histograms[j]
            )

            if distance <= threshold:
                union(i, j)

    # Build connected components.
    clusters = {}

    for i, path in enumerate(image_paths):
        root = find(i)
        clusters.setdefault(root, []).append(path)

    # Never return singleton clusters.
    return [
        members
        for members in clusters.values()
        if len(members) >= 2
    ]