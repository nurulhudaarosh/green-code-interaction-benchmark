def partition_points(points, k):
    """
    Sort 1D points, partition into k contiguous clusters minimizing WCSS.
    Returns (min_cost, boundaries) where boundaries is a list of start
    indices (0-based) of each cluster in sorted order.
    """
    n = len(points)
    if k < 1 or k > n:
        raise ValueError("k must satisfy 1 <= k <= n")

    # Sort points (stable; we only need values)
    x = sorted(points)

    # Prefix sums: P[i] = sum of x[0..i-1], Q[i] = sum of x[0..i-1]^2
    P = [0.0] * (n + 1)
    Q = [0.0] * (n + 1)
    for i in range(n):
        P[i + 1] = P[i] + x[i]
        Q[i + 1] = Q[i] + x[i] * x[i]

    def cost(l, r):
        """Inclusive cost of cluster x[l..r]."""
        cnt = r - l + 1
        s = P[r + 1] - P[l]
        sq = Q[r + 1] - Q[l]
        return sq - (s * s) / cnt

    INF = float("inf")
    # dp[j][i] = min cost partitioning first i points into j clusters
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    split = [[-1] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0

    for j in range(1, k + 1):
        for i in range(j, n + 1):
            best = INF
            best_t = -1
            # last cluster covers x[t .. i-1], t ranges from j-1 to i-1
            for t in range(j - 1, i):
                if dp[j - 1][t] == INF:
                    continue
                c = dp[j - 1][t] + cost(t, i - 1)
                if c < best:
                    best = c
                    best_t = t
            dp[j][i] = best
            split[j][i] = best_t

    # Reconstruct boundaries (start indices of each cluster)
    boundaries = []
    i = n
    for j in range(k, 0, -1):
        t = split[j][i]
        boundaries.append(t)
        i = t
    boundaries.reverse()

    return dp[k][n], boundaries


# ---------- deterministic self-test (no randomness) ----------
if __name__ == "__main__":
    # Example 1: simple
    pts = [1, 2, 3, 10, 11, 12]
    k = 2
    c, b = partition_points(pts, k)
    print("points:", sorted(pts))
    print("k =", k)
    print("min cost =", c)
    print("cluster start indices:", b)
    # Expected: clusters [1,2,3] and [10,11,12] -> boundaries [0, 3]

    # Example 2: k = n (each point its own cluster -> cost 0)
    c2, b2 = partition_points(pts, len(pts))
    print("\nk = n test -> cost =", c2, "boundaries =", b2)

    # Example 3: k = 1
    c3, b3 = partition_points(pts, 1)
    print("k = 1 test -> cost =", c3, "boundaries =", b3)

    # Example 4: known values
    pts4 = [0.0, 0.0, 0.0, 10.0, 10.0]
    c4, b4 = partition_points(pts4, 2)
    print("\npoints:", pts4, "k=2 -> cost =", c4, "boundaries =", b4)
    # Expect: clusters [0,0,0] and [10,10] -> cost 0, boundaries [0,3]