def kmeans_1d(points, k):
    n = len(points)
    if k <= 0 or k > n:
        raise ValueError("k must be between 1 and n")

    # Prefix sums
    pref = [0.0] * (n + 1)
    pref2 = [0.0] * (n + 1)
    for i, x in enumerate(points):
        pref[i + 1] = pref[i] + x
        pref2[i + 1] = pref2[i] + x * x

    def interval_cost(i, j):
        """Cost of points[i..j] inclusive."""
        cnt = j - i + 1
        s = pref[j + 1] - pref[i]
        s2 = pref2[j + 1] - pref2[i]
        return s2 - (s * s) / cnt

    INF = float('inf')
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    split = [[-1] * (n + 1) for _ in range(k + 1)]

    # Base: 1 cluster
    for i in range(1, n + 1):
        dp[1][i] = interval_cost(0, i - 1)
        split[1][i] = 0

    # DP for m >= 2 clusters
    for m in range(2, k + 1):
        for i in range(m, n + 1):  # need at least m points
            best = INF
            best_p = -1
            for p in range(m - 1, i):  # previous cut position
                c = dp[m - 1][p] + interval_cost(p, i - 1)
                if c < best:
                    best = c
                    best_p = p
            dp[m][i] = best
            split[m][i] = best_p

    # Reconstruct boundaries
    boundaries = []
    i = n
    for m in range(k, 0, -1):
        p = split[m][i]
        boundaries.append((p, i - 1))  # cluster covers [p, i-1]
        i = p
    boundaries.reverse()

    return dp[k][n], boundaries


# ---------------- Example usage ----------------
if __name__ == "__main__":
    pts = [1.0, 2.0, 3.0, 10.0, 11.0, 12.0, 20.0]
    k = 3
    cost, bounds = kmeans_1d(pts, k)
    print("Points:", pts)
    print("k =", k)
    print("Minimum cost:", cost)
    print("Cluster boundaries (start, end) inclusive:")
    for b in bounds:
        print(" ", b, "->", pts[b[0]:b[1] + 1])