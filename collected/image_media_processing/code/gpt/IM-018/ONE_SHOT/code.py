import os
from PIL import Image


def find_near_duplicates(input_dir, threshold):
    """
    Cluster images by normalized grayscale histogram L1 distance.

    Two images are connected when their normalized grayscale histogram
    L1 distance is <= threshold. Clusters are formed transitively using
    union-find.

    Returns:
        list[list[str]]: Clusters containing image file paths.
    """
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

    paths = [
        os.path.join(input_dir, name)
        for name in sorted(os.listdir(input_dir))
        if os.path.splitext(name)[1].lower() in image_exts
    ]

    def histogram(path):
        with Image.open(path) as img:
            gray = img.convert("L")
            hist = gray.histogram()

        total = sum(hist)
        if total == 0:
            return [0.0] * 256

        return [count / total for count in hist]

    histograms = [histogram(path) for path in paths]

    # Union-find structure.
    parent = list(range(len(paths)))
    rank = [0] * len(paths)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return

        if rank[ra] < rank[rb]:
            ra, rb = rb, ra

        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1

    # Connect every pair within the threshold.
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            distance = sum(
                abs(a - b)
                for a, b in zip(histograms[i], histograms[j])
            )

            if distance <= threshold:
                union(i, j)

    # Build transitive clusters.
    clusters = {}
    for i, path in enumerate(paths):
        root = find(i)
        clusters.setdefault(root, []).append(path)

    return list(clusters.values())