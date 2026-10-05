import os
import glob
import cv2
import numpy as np

class UnionFind:
    """Disjoint Set Union (DSU) to track connected components transitively."""
    def __init__(self, elements):
        self.parent = {el: el for el in elements}

    def find(self, item):
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])  # Path compression
        return self.parent[item]

    def union(self, item1, item2):
        root1 = self.find(item1)
        root2 = self.find(item2)
        if root1 != root2:
            self.parent[root2] = root1

    def get_clusters(self):
        clusters = {}
        for item in self.parent:
            root = self.find(item)
            clusters.setdefault(root, []).append(item)
        return [group for group in clusters.values() if len(group) > 1]


def compute_normalized_histogram(image_path, bins=256):
    """Loads an image in grayscale, computes its 1D histogram, and normalizes it."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    
    hist = cv2.calcHist([img], [0], None, [bins], [0, 256]).ravel()
    norm = np.linalg.norm(hist, ord=1)
    
    if norm == 0:
        return None
    
    return hist / norm


def find_near_duplicates(input_dir, threshold=0.1, bins=256):
    """
    Finds clusters of near-duplicate images in input_dir using normalized 
    grayscale histogram L1 distance and transitive Union-Find grouping.

    Parameters:
        input_dir (str): Path to directory containing images.
        threshold (float): L1 distance threshold below which images are merged. 
                           0.0 means identical histograms; typical range [0.05, 0.2].
        bins (int): Number of bins for the grayscale histogram.

    Returns:
        list[list[str]]: A list of clusters, where each cluster contains file paths 
                        of transitive near-duplicate images.
    """
    extensions = ('*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp', '*.tiff')
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(input_dir, ext)))
        image_paths.extend(glob.glob(os.path.join(input_dir, ext.upper())))
    
    image_paths = sorted(list(set(image_paths)))
    
    # 1. Precompute normalized histograms
    valid_paths = []
    histograms = []
    for path in image_paths:
        hist = compute_normalized_histogram(path, bins=bins)
        if hist is not None:
            valid_paths.append(path)
            histograms.append(hist)
            
    if not valid_paths:
        return []

    hist_matrix = np.array(histograms)  # Shape: (N, bins)
    
    # 2. Transitive grouping using Union-Find
    uf = UnionFind(valid_paths)
    num_images = len(valid_paths)

    # 3. Pairwise L1 distance comparison
    for i in range(num_images):
        for j in range(i + 1, num_images):
            # L1 distance: sum(|h1 - h2|)
            l1_dist = np.sum(np.abs(hist_matrix[i] - hist_matrix[j]))
            if l1_dist <= threshold:
                uf.union(valid_paths[i], valid_paths[j])

    # 4. Return grouped clusters (clusters with > 1 element)
    return uf.get_clusters()


# Example Usage:
if __name__ == "__main__":
    dir_path = "./sample_images"
    clusters = find_near_duplicates(dir_path, threshold=0.1)
    
    for idx, cluster in enumerate(clusters, start=1):
        print(f"Cluster {idx}:")
        for filepath in cluster:
            print(f"  - {filepath}")