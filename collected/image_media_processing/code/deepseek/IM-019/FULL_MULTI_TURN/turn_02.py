def find_fuzzy_duplicates(input_dir, hash_size=8, max_hamming=5):
    """
    Cluster images in input_dir by average-hash Hamming distance.
    ...
    """
    if hash_size < 1:
        raise ValueError("hash_size must be >= 1")

    total_bits = hash_size * hash_size
    if max_hamming < 0 or max_hamming > total_bits:
        raise ValueError(
            f"max_hamming must be between 0 and {total_bits} "
            f"(hash_size={hash_size} produces {total_bits}-bit hashes)"
        )

    extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}

    hashes = {}
    failures = []
    paths = []

    for name in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(name)[1].lower() not in extensions:
            continue
        try:
            hashes[path] = _average_hash(path, hash_size=hash_size)
            paths.append(path)
        except Exception as e:
            failures.append((path, str(e)))

    uf = _UnionFind()
    for p in paths:
        uf.add(p)

    n = len(paths)
    iterator = tqdm(range(n), desc="Comparing hashes", disable=(n < 200))
    for i in iterator:
        hi = hashes[paths[i]]
        for j in range(i + 1, n):
            if _hamming(hi, hashes[paths[j]]) <= max_hamming:
                uf.union(paths[i], paths[j])

    clusters_map = defaultdict(list)
    for p in paths:
        clusters_map[uf.find(p)].append(p)

    clusters = [sorted(group) for group in clusters_map.values() if len(group) >= 2]
    clusters.sort(key=len, reverse=True)

    if failures:
        import warnings
        warnings.warn(
            f"Skipped {len(failures)} unreadable file(s); "
            f"first: {failures[0][0]} ({failures[0][1]})"
        )

    return clusters