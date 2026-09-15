def partition_points(points, k):
    """
    Partition sorted 1D points into k contiguous clusters minimizing
    sum of squared deviations from cluster means.

    Returns:
        (min_cost, boundaries)
        boundaries = [0, b1, b2, ..., bk] where bk = n
    """
    n = len(points)
    if n == 0:
        return 0.0, [0]
    if k <= 0:
        raise ValueError("k must be positive")
    if k > n:
        raise ValueError("k cannot exceed number of points")

    # Prefix sums: P[i] = sum of points[0:i]
    # Prefix sum of squares: Q[i] = sum of points[0:i]^2
    P = [0.0] * (n + 1)
    Q = [0.0] * (n + 1)
    for i in range(n):
        P[i + 1] = P[i] + points[i]
        Q[i + 1] = Q[i] + points[i] * points[i]

    def interval_cost(i, j):
        """Cost of cluster points[i:j]."""
        m = j - i
        if m == 0:
            return 0.0
        s = P[j] - P[i]
        sq = Q[j] - Q[i]
        return sq - (s * s) / m

    INF = float('inf')

    # dp[t][j] = min cost to partition first j points into t clusters
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    split = [[-1] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0

    for t in range(1, k + 1):
        for j in range(t, n + 1):
            best = INF
            best_i = -1
            # Need at least t-1 points for t-1 clusters
            for i in range(t - 1, j):
                if dp[t - 1][i] == INF:
                    continue
                c = dp[t - 1][i] + interval_cost(i, j)
                if c < best:
                    best = c
                    best_i = i
            dp[t][j] = best
            split[t][j] = best_i

    # Reconstruct boundaries
    boundaries = [n]
    j = n
    for t in range(k, 0, -1):
        i = split[t][j]
        boundaries.append(i)
        j = i
    boundaries.reverse()

    return dp[k][n], boundaries


def main():
    # Example / test
    points = [1.0, 2.0, 3.0, 10.0, 11.0, 12.0]
    k = 2
    cost, bounds = partition_points(points, k)
    print(f"Points: {points}")
    print(f"k = {k}")
    print(f"Minimum cost: {cost}")
    print(f"Boundaries: {bounds}")
    # Show clusters
    for c in range(len(bounds) - 1):
        i, j = bounds[c], bounds[c + 1]
        cluster = points[i:j]
        mean = sum(cluster) / len(cluster)
        print(f"  Cluster {c + 1}: {cluster} (mean={mean:.3f})")

    # Additional test: k=1 should give variance * n
    cost1, b1 = partition_points(points, 1)
    mean_all = sum(points) / len(points)
    expected = sum((x - mean_all) ** 2 for x in points)
    print(f"\nk=1 cost: {cost1}, expected: {expected}")

    # k=n gives 0 cost
    cost_n, b_n = partition_points(points, len(points))
    print(f"k=n cost: {cost_n} (should be 0.0)")
    print(f"k=n boundaries: {b_n}")


if __name__ == "__main__":
    main()