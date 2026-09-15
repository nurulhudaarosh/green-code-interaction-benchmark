def partition_points(points, k):
    """
    Sort 1D points, partition into exactly k contiguous non-empty clusters
    minimizing within-cluster sum of squares (WCSS).

    Returns:
        (min_cost, boundaries)

    boundaries: list of k 0-based start indices of clusters in sorted order,
    chosen to be LEXICOGRAPHICALLY SMALLEST among all optimal partitions.

    Tie-break is explicit: at each DP cell, among equal-cost candidates we
    compare the full boundary lists and keep the lexicographically smallest.
    This makes the result independent of loop direction or comparator style.
    """
    n = len(points)
    if k < 1 or k > n:
        raise ValueError("k must satisfy 1 <= k <= n")

    x = sorted(points)

    P = [0.0] * (n + 1)   # sum of x[0..i-1]
    Q = [0.0] * (n + 1)   # sum of x[0..i-1]^2
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
    # best_bounds[j][i] = lex-smallest boundary list for dp[j][i]
    best_bounds = [[None] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0
    best_bounds[0][0] = []

    for j in range(1, k + 1):
        for i in range(j, n + 1):
            best = INF
            best_b = None
            for t in range(j - 1, i):
                if dp[j - 1][t] == INF:
                    continue
                c = dp[j - 1][t] + cost(t, i - 1)
                cand_b = best_bounds[j - 1][t] + [t]
                if c < best - 1e-12:
                    best = c
                    best_b = cand_b
                elif abs(c - best) <= 1e-12:
                    # Explicit lexicographic tie-break
                    if best_b is None or cand_b < best_b:
                        best = c
                        best_b = cand_b
            dp[j][i] = best
            best_bounds[j][i] = best_b

    return dp[k][n], best_bounds[k][n]


# ---------------- deterministic self-tests ----------------
if __name__ == "__main__":
    # --- Original behavior preserved ---
    c, b = partition_points([1, 2, 3, 10, 11, 12], 2)
    assert abs(c - 2.0) < 1e-9 and b == [0, 3], (c, b)

    c, b = partition_points([5, 1, 3, 2, 4], 5)
    assert c == 0.0 and b == [0, 1, 2, 3, 4], (c, b)

    c, b = partition_points([1, 2, 3], 1)
    assert abs(c - 2.0 / 3.0) < 1e-9 and b == [0], (c, b)

    # --- Explicit tie case: x=[0,2,4], k=2, both t=1 and t=2 give cost 2.0 ---
    # Lex-smallest boundaries: [0,1] (t=1) beats [0,2] (t=2).
    c, b = partition_points([0, 2, 4], 2)
    assert abs(c - 2.0) < 1e-9, c
    assert b == [0, 1], b

    # Another tie: x=[0,0,10,10], k=3
    # Partitions (all cost 0): [0],[0],[10,10] -> [0,1,2]
    #                          [0],[0,10],[10] -> [0,1,3]  (cost >0 actually)
    # Verify the true optimum and lex-smallest boundaries.
    c, b = partition_points([0, 0, 10, 10], 3)
    # Best cost 0 requires each cluster constant: only [0],[0],[10,10]
    # or [0,0],[10],[10]. Lex-smallest boundaries: [0,1,2].
    assert abs(c - 0.0) < 1e-9, c
    assert b == [0, 1, 2], b

    # --- Repeated values ---
    # All equal -> any split costs 0; lex-smallest boundaries are 0..k-1.
    c, b = partition_points([7, 7, 7, 7, 7], 3)
    assert abs(c - 0.0) < 1e-9, c
    assert b == [0, 1, 2], b

    # Repeated values with two groups
    c, b = partition_points([0.0, 0.0, 0.0, 10.0, 10.0], 2)
    assert abs(c - 0.0) < 1e-9, c
    # Optimal cost 0 requires [0,0,0] and [10,10] -> boundaries [0,3].
    assert b == [0, 3], b

    # Repeated values, k=1 -> single cluster
    c, b = partition_points([4, 4, 4, 4], 1)
    assert abs(c - 0.0) < 1e-9 and b == [0], (c, b)

    # Repeated values, k=n -> each point its own cluster
    c, b = partition_points([3, 3, 3], 3)
    assert abs(c - 0.0) < 1e-9 and b == [0, 1, 2], (c, b)

    # Mixed repeats with a clear optimum
    c, b = partition_points([1, 1, 1, 2, 2, 2, 10, 10, 10], 3)
    assert abs(c - 0.0) < 1e-9, c
    assert b == [0, 3, 6], b

    # --- Determinism check: repeated calls give identical results ---
    for _ in range(3):
        assert partition_points([0, 2, 4], 2) == (2.0, [0, 1])
        assert partition_points([7, 7, 7, 7, 7], 3)[1] == [0, 1, 2]

    # --- Lex-smallest tie-break is order-independent by construction ---
    # Construct a case with multiple ties across different j levels.
    # x=[0,2,4,6], k=2: t=1 -> [0],[2,4,6] cost 8.0
    #                   t=2 -> [0,2],[4,6] cost 2.0
    #                   t=3 -> [0,2,4],[6] cost 8.0
    # Unique optimum at t=2.
    c, b = partition_points([0, 2, 4, 6], 2)
    assert abs(c - 2.0) < 1e-9 and b == [0, 2], (c, b)

    print("All deterministic self-tests passed (repeats + ties).")