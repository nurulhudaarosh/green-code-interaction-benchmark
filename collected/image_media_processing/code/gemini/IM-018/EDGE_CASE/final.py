import os
import glob
import numpy as np
from PIL import Image

class UnionFind:
    def __init__(self, elements):
        self.parent = {el: el for el in elements}
        self.rank = {el: 0 for el in elements}

    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            # Union by rank
            if self.rank[root_i] < self.rank[root_j]:
                root_i, root_j = root_j, root_i
            self.parent[root_j] = root_i
            if self.rank[root_i] == self.rank[root_j]:
                self.rank[root_i] += 1

def compute_normalized_grayscale_histogram(image_path):
    """Loads an image, converts it to grayscale, and returns a 256-bin normalized histogram."""
    try:
        with Image.open(image_path) as img:
            gray_img = img.convert('L')
            hist = np.array(gray_img.histogram(), dtype=np.float64)
            total_pixels = hist.sum()
            if total_pixels > 0:
                hist /= total_pixels
            return hist
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def find_near_duplicates(input_dir, threshold=0.1):
    """
    Clusters near-duplicate images in input_dir based on normalized grayscale histogram L1 distance.
    
    Args:
        input_dir (str): Path to directory containing images.
        threshold (float): L1 distance threshold in [0.0, 1.0].
                           
    Returns:
        list of list of str: Groups of near-duplicate image file paths (each group size >= 2).
    """
    extensions = ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp', '*.tiff')
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(input_dir, ext)))
        image_paths.extend(glob.glob(os.path.join(input_dir, ext.upper())))
    
    image_paths = sorted(list(set(image_paths)))
    
    # Return empty list immediately if fewer than 2 total images found
    if len(image_paths) < 2:
        return []

    # Step 1: Precompute normalized histograms
    histograms = {}
    valid_paths = []
    for path in image_paths:
        hist = compute_normalized_grayscale_histogram(path)
        if hist is not None:
            histograms[path] = hist
            valid_paths.append(path)

    # Re-check valid images count after parsing
    if len(valid_paths) < 2:
        return []

    # Step 2: Initialize Union-Find structure
    uf = UnionFind(valid_paths)

    # Step 3: Compute pairwise L1 distances and merge clusters
    n = len(valid_paths)
    for i in range(n):
        path1 = valid_paths[i]
        hist1 = histograms[path1]
        for j in range(i + 1, n):
            path2 = valid_paths[j]
            hist2 = histograms[path2]

            # Normalized L1 distance in [0, 1] range: 0.5 * sum(|h1 - h2|)
            l1_distance = 0.5 * np.sum(np.abs(hist1 - hist2))

            if l1_distance <= threshold:
                uf.union(path1, path2)

    # Step 4: Gather clusters by root parent
    clusters = {}
    for path in valid_paths:
        root = uf.find(path)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(path)

    # Filter out singletons (only keep clusters with size >= 2)
    duplicate_groups = [group for group in clusters.values() if len(group) >= 2]

    return duplicate_groups