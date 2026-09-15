"""
PROBLEM
-------
Sort a list of one-dimensional points and partition them into k
CONTIGUOUS clusters so as to minimize the total sum of squared
deviations of each point from its own cluster's mean:

    cost = sum over clusters C of  sum_{x in C} (x - mean(C))**2

Because the points are 1-D and sorted, an optimal partition is always
contiguous (no cluster needs to "skip over" another), which makes an
exact dynamic-programming solution possible.

KEY CONSTRAINTS
----------------
- Input is a list/iterable of n real numbers.
- 1 <= k <= n.
- Clusters must be contiguous ranges of the sorted data and non-empty.
- Solution must be deterministic: no randomness, no network access,
  no external APIs/services, no human interaction.

REQUIRED OUTPUT
----------------
- The optimal (minimum) total sum-of-squares cost (float).
- Boundary indices [0, b_1, ..., b_{k-1}, n] into the SORTED points,
  such that cluster i = sorted_points[b_i : b_{i+1}].

ALGORITHM (prefix sums + interval-cost DP)
-------------------------------------------
1. Sort the points.
2. Prefix sums S[j] = sum_{t<j} x[t], Q[j] = sum_{t<j} x[t]**2, giving
   O(1) cost for any interval [i, j):
        cost(i, j) = Q[j] - Q[i] - (S[j] - S[i])**2 / (j - i)
   (identity: sum (x - mean)^2 = sum x^2 - (sum x)^2 / n)
3. DP over (clusters used, prefix length):
        dp[1][j] = cost(0, j)
        dp[m][j] = min_{i in [m-1, j-1]} dp[m-1][i] + cost(i, j)
4. Track argmin split points in a parent table; backtrack from
   dp[k][n] to recover exact boundaries.

Complexity: O(n^2 * k) time, O(n * k) space.
"""

from typing import List, Sequence, Tuple

INF = float("inf")


def _prefix_sums(sorted_points: Sequence[float]) -> Tuple[List[float], List[float]]:
    n = len(sorted_points)
    S = [0.0] * (n + 1)
    Q = [0.0] * (n + 1)
    for t in range(n):
        S[t + 1] = S[t] + sorted_points[t]
        Q[t + 1] = Q[t] + sorted_points[t] * sorted_points[t]
    return S, Q


def _interval_cost(S: List[float], Q: List[float], i: int, j: int) -> float:
    """Sum of squared deviations from the mean for sorted_points[i:j]."""
    n = j - i
    if n <= 0:
        return 0.0
    total = S[j] - S[i]
    total_sq = Q[j] - Q[i]
    return total_sq - (total * total) / n


def optimal_1d_kmeans(points: Sequence[float], k: int) -> Tuple[float, List[int]]:
    """
    Partition `points` into `k` contiguous clusters (after sorting) that
    minimize total within-cluster sum of squared deviations.

    Returns (cost, boundaries):
        cost       -- optimal total sum-of-squares cost (float)
        boundaries -- list of k+1 indices [0, b1, ..., b_{k-1}, n] into
                      the SORTED points; cluster i is
                      sorted_points[boundaries[i]:boundaries[i+1]]
    """
    n = len(points)
    if n == 0:
        raise ValueError("points must be non-empty")
    if not (1 <= k <= n):
        raise ValueError(f"k must satisfy 1 <= k <= n (got k={k}, n={n})")

    sorted_points = sorted(points)
    S, Q = _prefix_sums(sorted_points)

    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    parent = [[-1] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0

    for m in range(1, k + 1):
        for j in range(m, n + 1):
            best_cost = INF
            best_i = -1
            for i in range(m - 1, j):
                prev = dp[m - 1][i]
                if prev == INF:
                    continue
                c = prev + _interval_cost(S, Q, i, j)
                if c < best_cost:
                    best_cost = c
                    best_i = i
            dp[m][j] = best_cost
            parent[m][j] = best_i

    total_cost = dp[k][n]
    if total_cost == INF:
        raise RuntimeError("no valid partition found (unexpected)")

    boundaries = [n]
    j = n
    for m in range(k, 0, -1):
        i = parent[m][j]
        boundaries.append(i)
        j = i
    boundaries.reverse()

    return total_cost, boundaries


def clusters_from_boundaries(
    points: Sequence[float], boundaries: Sequence[int]
) -> List[List[float]]:
    """Convenience helper: materialize the actual cluster point-lists."""
    sorted_points = sorted(points)
    return [
        sorted_points[boundaries[i]:boundaries[i + 1]]
        for i in range(len(boundaries) - 1)
    ]


if __name__ == "__main__":
    # Deterministic demonstration (no randomness / no external input).
    demo_points = [1, 2, 3, 10, 11, 12, 25, 26, 27, 28]
    demo_k = 3

    cost, boundaries = optimal_1d_kmeans(demo_points, demo_k)
    clusters = clusters_from_boundaries(demo_points, boundaries)

    print(f"Sorted points: {sorted(demo_points)}")
    print(f"k = {demo_k}")
    print(f"Optimal cost:  {cost:.6f}")
    print(f"Boundaries:    {boundaries}")
    print("Clusters:")
    for idx, c in enumerate(clusters):
        mean = sum(c) / len(c)
        print(f"  cluster {idx}: {c}  (mean={mean:.3f})")