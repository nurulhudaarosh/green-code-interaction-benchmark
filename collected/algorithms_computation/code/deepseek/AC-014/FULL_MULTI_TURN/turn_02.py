def partition_points(points, k):
    """
    Sort 1D points, partition into exactly k contiguous non-empty clusters
    minimizing within-cluster sum of squares (WCSS).

    Returns (min_cost, boundaries) where boundaries is a list of the
    k start indices (0-based) of each cluster in sorted order.

    Deterministic tie handling:
      Among all partitions achieving the minimal cost, return the one whose
      boundary list is lexicographically smallest. This is realized by the
      recurrence choosing the LARGEST feasible split index t at every DP cell
      (achieved by iterating t ascending and using '<=' instead of '<'),
      which is independent of loop direction.
    """
    n = len(points)
    if k < 1 or k > n:
        raise ValueError("k must satisfy 1 <= k <= n")

    x = sorted(points)

    # Prefix sums: P[i] = sum x[0..i-1], Q[i] = sum x[0..i-1]^2
    P = [0.0] * (n + 1)
    Q = [0.0] * (n + 1)
    for i in range(n):
        P[i + 1] = P[i] + x[i]
        Q[i + 1] = Q[i] + x[i] * x[i]

    def cost(l, r):
        """Inclusive WCSS of x[l..r]."""
        cnt = r - l + 1
        s = P[r + 1] - P[l]
        sq = Q[r + 1] - Q[l]
        return sq - (s * s) / cnt

    INF = float("inf")
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    split = [[-1] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0

    for j in range(1, k + 1):
        for i in range(j, n + 1):
            best = INF
            best_t = -1
            # t is the start of the last cluster; t in [j-1, i-1].
            # Using '<=' picks the LARGEST optimal t, giving the
            # lexicographically smallest boundary list. This is explicit
            # and order-independent.
            for t in range(j - 1, i):
                if dp[j - 1][t] == INF:
                    continue
                c = dp[j - 1][t] + cost(t, i - 1)
                if c <= best:          # '<=' => prefer larger t
                    best = c
                    best_t = t
            dp[j][i] = best
            split[j][i] = best_t

    boundaries = []
    i = n
    for j in range(k, 0, -1):
        t = split[j][i]
        boundaries.append(t)
        i = t
    boundaries.reverse()

    return dp[k][n], boundaries


# ---------------- deterministic self-tests ----------------
if __name__ == "__main__":
    # Tie case: x=[0,2,4], k=2 -> cost 2.0 at t=1 and t=2.
    # Documented rule (lex-smallest boundaries) -> [0, 1].
    c, b = partition_points([0, 2, 4], 2)
    assert c == 2.0 and b == [0, 1], (c, b)

    # Two well-separated groups
    c, b = partition_points([1, 2, 3, 10, 11, 12], 2)
    assert abs(c - 2.0) < 1e-9 and b == [0, 3], (c, b)

    # k = n -> each point its own cluster, cost 0
    c, b = partition_points([5, 1, 3, 2, 4], 5)
    assert c == 0.0 and b == [0, 1, 2, 3, 4], (c, b)

    # k = 1 -> single cluster
    c, b = partition_points([1, 2, 3], 1)
    assert abs(c - 2.0 / 3.0) < 1e-9 and b == [0], (c, b)

    # Repeated values
    c, b = partition_points([0.0, 0.0, 0.0, 10.0, 10.0], 2)
    assert c == 0.0 and b == [0, 3], (c, b)

    # Large-ish deterministic case: 20 equally spaced points, k=4
    pts = list(range(20))
    c, b = partition_points(pts, 4)
    # Equal-size clusters [0..4],[5..9],[10..14],[15..19] -> 4*10 = 40
    assert abs(c - 40.0) < 1e-9 and b == [0, 5, 10, 15], (c, b)

    print("All deterministic self-tests passed.")
    print("Example:", partition_points([0, 2, 4], 2))