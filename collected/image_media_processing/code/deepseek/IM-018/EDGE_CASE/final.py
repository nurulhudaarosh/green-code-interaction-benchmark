def find_near_duplicates(input_dir, threshold):
    """
    Cluster images in `input_dir` whose normalized grayscale histograms have
    L1 distance <= `threshold`.

    Transitive grouping: if A~B and B~C, then A, B, C are in the same cluster
    even if A and C exceed the threshold (union-find).

    Parameters
    ----------
    input_dir : str | os.PathLike
        Directory to scan (recursively) for images.
    threshold : float
        Maximum L1 distance between normalized histograms (range 0.0 - 2.0).

    Returns
    -------
    list[list[str]]
        A list of clusters. Each cluster is a list of file paths. Only clusters
        with 2+ members are returned (singletons are dropped). Sorted by
        descending cluster size, then by first path.

    Notes
    -----
    - An empty directory, a directory with no readable images, or a directory
      containing exactly one image all return ``[]``: a cluster requires at
      least two members.
    - Files that fail to load (corrupt, unsupported codec, etc.) are silently
      skipped and do not contribute to the cluster count.
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    # 1. Collect image paths (recursive)
    paths = sorted(
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )

    # 2. Compute histograms; unreadable files are skipped.
    hists = []
    valid_paths = []
    for p in paths:
        h = _load_histogram(p)
        if h is not None:
            hists.append(h)
            valid_paths.append(p)

    # 3. Edge-case guard: need at least two *loadable* images to form a cluster.
    #    Covers 0 images, 1 image, and "many files but only 1 readable image".
    #    Must run BEFORE np.vstack (which rejects an empty list) and before
    #    the pairwise loop (which would yield an empty combinations iterator
    #    anyway, but this makes the intent explicit and avoids wasted work).
    n = len(valid_paths)
    if n < 2:
        return []

    hists = np.vstack(hists)  # shape (n, HIST_BINS), n >= 2

    # 4. Union-find over all pairs; O(n^2) comparisons.
    uf = UnionFind(n)
    for i, j in combinations(range(n), 2):
        d = np.abs(hists[i] - hists[j]).sum()
        if d <= threshold:
            uf.union(i, j)

    # 5. Group members by root.
    clusters = {}
    for i in range(n):
        root = uf.find(i)
        clusters.setdefault(root, []).append(str(valid_paths[i]))

    # 6. Keep only clusters with 2+ members, then sort.
    result = [sorted(members) for members in clusters.values() if len(members) > 1]
    result.sort(key=lambda c: (-len(c), c[0]))
    return result