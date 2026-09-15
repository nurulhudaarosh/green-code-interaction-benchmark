def cluster_1d(points, k):
    """
    Sort 1D points and partition into k contiguous clusters minimizing
    sum of squared deviations from each cluster mean.

    Returns (min_cost, boundaries) where boundaries is a list of k indices:
    the start index of each cluster in the sorted array (0-based).
    The last cluster ends at len(points)-1.
    """
    n = len(points)
    if not (1 <= k <= n):
        raise ValueError("k must satisfy 1 <= k <= n")

    # Sort points (deterministic)
    xs = sorted(float(p) for p in points)

    # Prefix sums: P[i] = sum of xs[0..i-1], P[0] = 0
    P = [0.0] * (n + 1)
    Q = [0.0] * (n + 1)  # prefix sum of squares
    for i, x in enumerate(xs):
        P[i + 1] = P[i] + x
        Q[i + 1] = Q[i] + x * x

    def interval_cost(i, j):
        """Cost of cluster xs[i..j] (inclusive)."""
        cnt = j - i + 1
        s = P[j + 1] - P[i]
        sq = Q[j + 1] - Q[i]
        # sum of squared deviations from mean = sq - s^2 / cnt
        return sq - (s * s) / cnt

    INF = float('inf')

    # dp[m][i]: min cost for first i points into m clusters (i points used)
    # m from 1..k, i from m..n
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    parent = [[-1] * (n + 1) for _ in range(k + 1)]

    # Base: m = 1
    for i in range(1, n + 1):
        dp[1][i] = interval_cost(0, i - 1)
        parent[1][i] = 0

    # Fill DP
    for m in range(2, k + 1):
        for i in range(m, n + 1):
            best_cost = INF
            best_t = -1
            # last cluster is xs[t..i-1], previous m-1 clusters cover xs[0..t-1]
            for t in range(m - 1, i):
                prev = dp[m - 1][t]
                if prev == INF:
                    continue
                c = prev + interval_cost(t, i - 1)
                if c < best_cost:
                    best_cost = c
                    best_t = t
            dp[m][i] = best_cost
            parent[m][i] = best_t

    # Reconstruct boundaries (start indices of clusters)
    boundaries = [0] * k
    i = n
    for m in range(k, 0, -1):
        t = parent[m][i]
        boundaries[m - 1] = t
        i = t

    return dp[k][n], boundaries


# Example usage
if __name__ == "__main__":
    data = [1, 2, 3, 10, 11, 12, 20]
    k = 3
    cost, bounds = cluster_1d(data, k)
    xs = sorted(data)
    print("Sorted points:", xs)
    print("Min cost:", cost)
    print("Cluster start indices:", bounds)
    for idx, start in enumerate(bounds):
        end = bounds[idx + 1] - 1 if idx + 1 < len(bounds) else len(xs) - 1
        print(f"Cluster {idx+1}: indices [{start}, {end}] -> {xs[start:end+1]}")