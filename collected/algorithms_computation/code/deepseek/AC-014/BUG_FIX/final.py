def cluster_points(points, k, tol=1e-12):
    """
    Sort 1D points and partition into k contiguous clusters
    minimizing sum of squared deviations from cluster means.

    Deterministic tie handling: when two splits yield costs within `tol`,
    the smaller split index j is chosen.

    Returns:
        (min_cost, boundaries)
        boundaries: [0, b1, ..., n] with cluster t = [boundaries[t], boundaries[t+1])
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
        c = s2 - (s * s) / m
        # Clamp tiny negative values from rounding to 0
        return c if c > 0.0 else 0.0

    INF = float("inf")
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    parent = [[-1] * (n + 1) for _ in range(k + 1)]

    for i in range(1, n + 1):
        dp[1][i] = interval_cost(0, i)

    for t in range(2, k + 1):
        for i in range(t, n + 1):
            best = INF
            best_j = -1
            for j in range(t - 1, i):
                cand = dp[t - 1][j] + interval_cost(j, i)
                # Deterministic tie handling: prefer smaller j.
                if cand < best - tol:
                    best = cand
                    best_j = j
                elif cand <= best + tol and j < best_j:
                    # Within tolerance: keep smaller j.
                    # (Only relevant if a later j is within tol of best.)
                    best = min(best, cand)
                    best_j = j
            dp[t][i] = best
            parent[t][i] = best_j

    # Reconstruct boundaries
    boundaries = [n]
    i = n
    for t in range(k, 1, -1):
        j = parent[t][i]
        if j < 0:
            raise RuntimeError("DP reconstruction failed (no valid parent)")
        boundaries.append(j)
        i = j
    boundaries.append(0)
    boundaries.reverse()

    return dp[k][n], boundaries