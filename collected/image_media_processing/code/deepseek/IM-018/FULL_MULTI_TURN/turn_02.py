def find_near_duplicates(input_dir, threshold, bins=256, size=(256, 256), verbose=False):
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    paths = sorted(
        str(p) for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if verbose:
        print(f"Found {len(paths)} image(s) in {input_dir}")

    valid_paths, histograms = [], []
    for p in paths:
        try:
            histograms.append(compute_histogram(p, bins=bins, size=size))
            valid_paths.append(p)
        except Exception as e:
            if verbose:
                print(f"  Skipping {p}: {e}")

    n = len(valid_paths)
    if n < 2:
        return []

    stacked = np.stack(histograms, axis=0)  # (n, bins)

    # --- Step 1: compute all pairwise L1 distances below threshold ---
    # Explicit (i, j) pairs make the union-find input obvious.
    close_pairs = []
    for i in range(n):
        # L1 distance from image i to every image j > i
        diffs = np.abs(stacked[i + 1:] - stacked[i]).sum(axis=1)
        for offset in np.nonzero(diffs <= threshold)[0]:
            j = i + 1 + int(offset)
            close_pairs.append((i, j))

    if verbose:
        print(f"Found {len(close_pairs)} close pair(s) at threshold {threshold}")

    # --- Step 2: transitive closure via union-find ---
    # Each union merges two components; chained pairs (A-B, B-C) collapse
    # into a single component {A, B, C} even if A-C was never close.
    uf = UnionFind(n)
    for i, j in close_pairs:
        uf.union(i, j)

    # --- Step 3: collect components and drop singletons ---
    clusters = []
    for members in uf.groups().values():
        if len(members) >= 2:
            clusters.append(sorted(valid_paths[m] for m in members))

    clusters.sort(key=lambda c: (-len(c), c[0]))
    return clusters