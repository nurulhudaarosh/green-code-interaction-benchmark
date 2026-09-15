"""
PROBLEM
-------
Given a set of one-dimensional real-valued points and an integer k, sort the
points and partition them into k contiguous (in sorted order) clusters such
that the sum over all clusters of the squared deviations of each point from
its own cluster mean (i.e. the within-cluster sum of squares, WCSS) is
minimized.

Because the points are one-dimensional, the optimal k-way partition of the
*sorted* sequence is always contiguous (an interval partition) — no optimal
clustering can "interleave" points from different clusters. This lets us
solve the problem exactly with dynamic programming instead of resorting to
heuristics like Lloyd's algorithm (k-means), which only guarantees a local
optimum.

KEY CONSTRAINTS
----------------
1. Input is a 1-D list of numbers (n points), and an integer k (1 <= k <= n).
2. Clusters must be contiguous intervals of the *sorted* point sequence.
3. Objective: minimize sum_{c=1..k} sum_{x in cluster c} (x - mean(cluster c))^2
4. The algorithm must be deterministic: same input -> same output, every run.
   No randomness, no network/API calls, no external services, no human input.
5. Standard library only.

REQUIRED OUTPUT
----------------
- total_cost: the minimized sum of squared deviations (float).
- boundaries: the final cut points, as a sorted list of k+1 indices
  [0, b1, b2, ..., b_{k-1}, n] into the *sorted* point array, such that
  cluster i occupies sorted_points[boundaries[i]:boundaries[i+1]].

ALGORITHM
---------
1. Sort the points.
2. Build prefix sums S[i] = sum of first i sorted points, and prefix sums of
   squares Q[i] = sum of squares of first i sorted points.
3. For any interval [i, j) of the sorted array, its optimal (variance) cost
   as a single cluster is computable in O(1) via:
       n_ij   = j - i
       sum_ij = S[j] - S[i]
       sq_ij  = Q[j] - Q[i]
       cost(i, j) = sq_ij - (sum_ij ** 2) / n_ij      (for n_ij > 0)
   This is the standard identity sum((x - mean)^2) = sum(x^2) - (sum(x))^2/n.
4. Dynamic programming over "number of clusters used" and "prefix length":
       dp[c][j] = minimum total cost of partitioning the first j sorted
                  points into exactly c contiguous clusters
       dp[0][0] = 0 ;  dp[0][j>0] = infinity
       dp[c][j] = min over i in [c-1, j-1] of dp[c-1][i] + cost(i, j)
   Track the optimal split point i (parent[c][j]) to reconstruct boundaries.
5. The answer is dp[k][n]; boundaries are recovered by walking parent
   pointers backward from (k, n) to (0, 0).

Complexity: O(k * n^2) time, O(k * n) space — exact and fully deterministic.
"""

from typing import List, Tuple
import math


def cluster_1d(points: List[float], k: int) -> Tuple[float, List[int]]:
    """
    Partition 1-D points into k contiguous clusters minimizing the sum of
    squared deviations from each cluster's mean.

    Returns:
        total_cost: float, the minimized sum of squared deviations.
        boundaries: List[int] of length k+1, indices into the sorted point
                    array marking cluster boundaries (boundaries[0] == 0,
                    boundaries[-1] == n). Cluster i is
                    sorted_points[boundaries[i]:boundaries[i+1]].
    """
    if not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer")
    n = len(points)
    if n == 0:
        raise ValueError("points must be non-empty")
    if k > n:
        raise ValueError("k cannot exceed the number of points")

    sorted_points = sorted(points)

    # Prefix sums of values and of squares (length n+1, index 0 = empty prefix)
    prefix_sum = [0.0] * (n + 1)
    prefix_sqsum = [0.0] * (n + 1)
    for idx in range(1, n + 1):
        v = sorted_points[idx - 1]
        prefix_sum[idx] = prefix_sum[idx - 1] + v
        prefix_sqsum[idx] = prefix_sqsum[idx - 1] + v * v

    def interval_cost(i: int, j: int) -> float:
        """Cost of a single cluster covering sorted_points[i:j], O(1)."""
        m = j - i
        if m <= 0:
            return 0.0
        s = prefix_sum[j] - prefix_sum[i]
        sq = prefix_sqsum[j] - prefix_sqsum[i]
        cost = sq - (s * s) / m
        # Guard against tiny negative values from floating-point rounding.
        return cost if cost > 0.0 else 0.0

    INF = math.inf

    # dp[c][j]: min cost partitioning first j points into c clusters
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    parent = [[-1] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0

    for c in range(1, k + 1):
        for j in range(c, n + 1):
            best_cost = INF
            best_i = -1
            # i must leave at least (c-1) points for the previous clusters
            # and at least 1 point for this cluster: i in [c-1, j-1]
            for i in range(c - 1, j):
                prev = dp[c - 1][i]
                if prev == INF:
                    continue
                total = prev + interval_cost(i, j)
                if total < best_cost:
                    best_cost = total
                    best_i = i
            dp[c][j] = best_cost
            parent[c][j] = best_i

    total_cost = dp[k][n]
    if total_cost == INF:
        raise RuntimeError("No valid partition found (unexpected)")

    # Reconstruct boundaries by walking parent pointers backward
    boundaries = [n]
    c, j = k, n
    while c > 0:
        i = parent[c][j]
        boundaries.append(i)
        j = i
        c -= 1
    boundaries.reverse()

    return total_cost, boundaries


if __name__ == "__main__":
    # Deterministic demonstration (no randomness, no external I/O).
    data = [1.0, 2.0, 3.0, 10.0, 11.0, 12.0, 25.0, 26.0, 100.0]
    k = 4

    cost, bounds = cluster_1d(data, k)
    sorted_data = sorted(data)

    print(f"Sorted points : {sorted_data}")
    print(f"k              : {k}")
    print(f"Total cost     : {cost}")
    print(f"Boundaries     : {bounds}")
    print("Clusters:")
    for idx in range(len(bounds) - 1):
        lo, hi = bounds[idx], bounds[idx + 1]
        print(f"  Cluster {idx}: {sorted_data[lo:hi]}")