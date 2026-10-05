import os
from collections import defaultdict
import cv2
import numpy as np


class UnionFind:
    """Disjoint Set Union (DSU) data structure with path compression."""

    def __init__(self, elements):
        self.parent = {el: el for el in elements}

    def find(self, i):
        # Path compression: recursively point nodes directly to the root
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j


def compute_normalized_histogram(image_path, bins=256):
    """Loads an image in grayscale and returns its L1-normalized histogram."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None

    hist = cv2.calcHist([img], [0], None, [bins], [0, 256])
    hist = cv2.normalize(hist, hist, alpha=1, beta=0, norm_type=cv2.NORM_L1)
    return hist


def find_near_duplicates(input_dir, threshold=0.1):
    """Clusters images in input_dir based on normalized grayscale histogram L1 distance

    with transitive union-find grouping.
    """
    valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff")
    image_files = [
        f
        for f in os.listdir(input_dir)
        if f.lower().endswith(valid_extensions)
    ]

    # 1. Compute normalized grayscale histogram for each valid image
    histograms = {}
    for filename in image_files:
        filepath = os.path.join(input_dir, filename)
        hist = compute_normalized_histogram(filepath)
        if hist is not None:
            histograms[filename] = hist

    valid_images = list(histograms.keys())
    uf = UnionFind(valid_images)

    # 2. Pairwise comparison: merge sets whenever distance <= threshold
    n = len(valid_images)
    for i in range(n):
        for j in range(i + 1, n):
            img_a = valid_images[i]
            img_b = valid_images[j]

            l1_dist = cv2.compareHist(
                histograms[img_a], histograms[img_b], cv2.HISTCMP_L1
            )

            # If pairwise distance is within threshold, unite their sets transitively
            if l1_dist <= threshold:
                uf.union(img_a, img_b)

    # 3. Transitive Resolution: gather all elements under their canonical root
    clusters_map = defaultdict(list)
    for img in valid_images:
        # calling find(img) forces full path compression to the canonical representative root
        root = uf.find(img)
        clusters_map[root].append(img)

    # 4. Filter to return only clusters with >= 2 images
    duplicate_clusters = [
        group for group in clusters_map.values() if len(group) > 1
    ]

    return duplicate_clusters