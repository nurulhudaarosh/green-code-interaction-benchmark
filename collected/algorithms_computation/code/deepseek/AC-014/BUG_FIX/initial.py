def cluster_points(points, k):
    """
    Sort 1D points and partition into k contiguous clusters
    minimizing sum of squared deviations from cluster means.

    Returns:
        (min_cost, boundaries)
        boundaries: list of k+1 indices [0, b1, b2, ..., n]
                    where cluster t covers [boundaries[t], boundaries[t+1])
    """
    n = len(points)
    if k < 1 or k > n:
        raise ValueError("Require 1 <= k <= n")

    xs = sorted(points)

    # Prefix sums of x and x^2 for O(1) interval cost
    pref = [0.0] * (n + 1)
    pref2 = [0.0] * (n + 1)
    for i, v in enumerate(xs):
        pref[i + 1] = pref[i] + v
        pref2[i + 1] = pref2[i] + v * v

    def interval_cost(i, j):
        # cost of cluster xs[i:j]
        m = j - i
        s = pref[j] - pref[i]
        s2 = pref2[j] - pref2[i]
        return s2 - (s * s) / m

    # dp[t][i] = min cost to cluster first i points into t groups
    INF = float("inf")
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    # parent[t][i] = best split point j for dp[t][i]
    parent = [[-1] * (n + 1) for _ in range(k + 1)]

    for i in range(1, n + 1):
        dp[1][i] = interval_cost(0, i)

    for t in range(2, k + 1):
        # Need at least t points to form t clusters
        for i in range(t, n + 1):
            best = INF
            best_j = -1
            # Previous partition must have at least t-1 points
            for j in range(t - 1, i):
                cand = dp[t - 1][j] + interval_cost(j, i)
                if cand < best:
                    best = cand
                    best_j = j
            dp[t][i] = best
            parent[t][i] = best_j

    # Reconstruct boundaries
    boundaries = [n]
    i = n
    for t in range(k, 1, -1):
        j = parent[t][i]
        boundaries.append(j)
        i = j
    boundaries.append(0)
    boundaries.reverse()

    return dp[k][n], boundaries


if __name__ == "__main__":
    # Example / self-test
    pts = [3.0, 1.0, 4.0, 1.5, 9.0, 10.0, 2.0]
    k = 3
    cost, bounds = cluster_points(pts, k)

    xs = sorted(pts)
    print("Sorted points:", xs)
    print(f"Minimum cost for k={k}: {cost:.6f}")
    print("Boundaries:", bounds)
    for t in range(k):
        lo, hi = bounds[t], bounds[t + 1]
        cluster = xs[lo:hi]
        mean = sum(cluster) / len(cluster)
        print(f"  Cluster {t+1}: {cluster}  mean={mean:.4f}")

    # Sanity check: k=1 cost should equal variance * n
    c1, _ = cluster_points(pts, 1)
    m = sum(xs) / len(xs)
    expected = sum((v - m) ** 2 for v in xs)
    print("\nk=1 cost check:", c1, "expected:", expected)

    # Sanity check: k=n cost should be 0
    cn, bn = cluster_points(pts, len(pts))
    print("k=n cost:", cn, "boundaries:", bn)