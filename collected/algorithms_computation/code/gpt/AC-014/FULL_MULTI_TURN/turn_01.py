"""
Problem Restatement
-------------------
Given one-dimensional points, sort them in nondecreasing order and partition
the sorted points into exactly k non-empty contiguous clusters.

For each cluster, its cost is the sum of squared deviations of its points
from that cluster's mean:

    cost(cluster) = sum((x - mean(cluster)) ** 2)

The goal is to minimize the total cost across all k clusters.

Return:
    - the minimum total cost
    - the final boundary indices of the k clusters

Key Constraints / Requirements
------------------------------
1. Points are one-dimensional numeric values.
2. Points must be sorted before clustering.
3. Clusters must be contiguous in the sorted order.
4. Exactly k non-empty clusters are required.
5. The objective is the sum of squared deviations from each cluster mean.
6. The solution must be deterministic.
7. For equal-cost choices, choose the smaller split index to make the result
   deterministic.
8. Use only the Python standard library.
9. No network access, APIs, external services, randomness, or human input.

Required Output
---------------
A dictionary containing:
    {
        "cost": minimum total clustering cost,
        "boundaries": final boundary indices
    }

Boundary convention:
    boundaries contains the zero-based ending index of each cluster.

Example:
    sorted points = [1, 2, 10, 11]
    boundaries = [1, 3]

means:
    cluster 1 -> indices 0..1 -> [1, 2]
    cluster 2 -> indices 2..3 -> [10, 11]


Algorithm
---------
1. Sort the points.
2. Build prefix sums:
       prefix_sum[i]  = sum of first i points
       prefix_sq[i]   = sum of squares of first i points

3. For any interval [left, right], calculate its squared-deviation cost
   in O(1):

       sum(x^2) - sum(x)^2 / count

4. Use interval-cost dynamic programming.

   dp[c][i] = minimum cost for partitioning the first i sorted points
               into exactly c clusters.

   Transition:
       dp[c][i] = min(
           dp[c-1][split] + interval_cost(split, i-1)
       )

   where:
       c-1 <= split < i

5. Store the split that gives the best cost. If two choices have the same
   cost, choose the smaller split index.

6. Backtrack from dp[k][n] to recover the final cluster boundaries.

Time Complexity
---------------
Sorting:       O(n log n)
DP:            O(k * n^2)
Memory:        O(k * n)

The interval cost itself is O(1) because of the prefix sums.
"""

from math import isclose


def one_dimensional_k_cluster(points, k):
    """
    Partition one-dimensional points into exactly k contiguous clusters
    after sorting.

    Returns:
        {
            "cost": float,
            "boundaries": list[int]
        }

    Boundary indices are zero-based ending indices in the sorted array.
    """

    # -------------------------
    # Validate input
    # -------------------------
    n = len(points)

    if n == 0:
        raise ValueError("points must not be empty")

    if not 1 <= k <= n:
        raise ValueError("k must satisfy 1 <= k <= len(points)")

    # -------------------------
    # Sort points
    # -------------------------
    values = sorted(points)

    # -------------------------
    # Prefix sums
    # -------------------------
    prefix_sum = [0.0] * (n + 1)
    prefix_sq = [0.0] * (n + 1)

    for i, x in enumerate(values, start=1):
        x = float(x)
        prefix_sum[i] = prefix_sum[i - 1] + x
        prefix_sq[i] = prefix_sq[i - 1] + x * x

    # -------------------------
    # Interval cost
    # -------------------------
    # Uses half-open interval [left, right).
    #
    # SSE = sum(x^2) - sum(x)^2 / count
    # -------------------------
    def interval_cost(left, right):
        count = right - left

        if count <= 0:
            return 0.0

        total = prefix_sum[right] - prefix_sum[left]
        total_sq = prefix_sq[right] - prefix_sq[left]

        cost = total_sq - (total * total) / count

        # Avoid tiny negative values caused by floating-point arithmetic.
        if cost < 0.0 and abs(cost) < 1e-12:
            cost = 0.0

        return cost

    INF = float("inf")

    # dp[c][i]:
    # minimum cost for first i points using exactly c clusters.
    dp = [[INF] * (n + 1) for _ in range(k + 1)]

    # parent[c][i]:
    # split position used to obtain dp[c][i].
    parent = [[-1] * (n + 1) for _ in range(k + 1)]

    dp[0][0] = 0.0

    # -------------------------
    # Dynamic programming
    # -------------------------
    for clusters in range(1, k + 1):

        # Need at least 'clusters' points for 'clusters' non-empty clusters.
        for i in range(clusters, n + 1):

            best_cost = INF
            best_split = -1

            # The previous clusters occupy [0, split).
            # The final cluster occupies [split, i).
            for split in range(clusters - 1, i):

                previous = dp[clusters - 1][split]

                if previous == INF:
                    continue

                candidate = previous + interval_cost(split, i)

                # Deterministic tie-breaking:
                # smaller split index wins.
                if candidate < best_cost:
                    best_cost = candidate
                    best_split = split
                elif candidate == best_cost:
                    if best_split == -1 or split < best_split:
                        best_split = split

            dp[clusters][i] = best_cost
            parent[clusters][i] = best_split

    # -------------------------
    # Recover cluster boundaries
    # -------------------------
    boundaries = []

    current_i = n

    for clusters in range(k, 0, -1):
        split = parent[clusters][current_i]

        if split == -1:
            raise RuntimeError("Failed to reconstruct clustering")

        # The current cluster is [split, current_i).
        #
        # Its inclusive ending index is current_i - 1.
        boundaries.append(current_i - 1)

        current_i = split

    boundaries.reverse()

    return {
        "cost": dp[k][n],
        "boundaries": boundaries,
    }


# ============================================================
# Tests
# ============================================================

def run_tests():
    # Test 1: Simple two-cluster example.
    result = one_dimensional_k_cluster([1, 2, 10, 11], 2)

    assert result["boundaries"] == [1, 3]
    assert isclose(result["cost"], 1.0)


    # Test 2: One cluster.
    result = one_dimensional_k_cluster([1, 2, 3], 1)

    assert result["boundaries"] == [2]
    assert isclose(result["cost"], 2.0)


    # Test 3: k == n.
    # Every point becomes its own cluster, so total cost is zero.
    result = one_dimensional_k_cluster([5, 1, 3], 3)

    assert result["boundaries"] == [0, 1, 2]
    assert isclose(result["cost"], 0.0)


    # Test 4: Repeated values.
    result = one_dimensional_k_cluster([1, 1, 1, 10, 10, 10], 2)

    assert result["boundaries"] == [2, 5]
    assert isclose(result["cost"], 0.0)


    # Test 5: Negative values.
    result = one_dimensional_k_cluster([-5, -4, 10, 11], 2)

    assert result["boundaries"] == [1, 3]
    assert isclose(result["cost"], 1.0)


    # Test 6: Deterministic tie case.
    #
    # For [0, 2, 4] with two clusters:
    #
    # split = 1:
    #   [0] and [2,4] -> 2
    #
    # split = 2:
    #   [0,2] and [4] -> 2
    #
    # Equal cost => smaller split index must be selected.
    result = one_dimensional_k_cluster([0, 2, 4], 2)

    assert result["boundaries"] == [0, 2]
    assert isclose(result["cost"], 2.0)


    # Test 7: Unsorted input must be sorted first.
    result = one_dimensional_k_cluster([11, 1, 10, 2], 2)

    assert result["boundaries"] == [1, 3]
    assert isclose(result["cost"], 1.0)


    # Test 8: All points identical.
    result = one_dimensional_k_cluster([7, 7, 7, 7], 2)

    assert result["cost"] == 0.0
    assert len(result["boundaries"]) == 2


    # Test 9: Invalid k.
    try:
        one_dimensional_k_cluster([1, 2, 3], 0)
        assert False, "Expected ValueError"
    except ValueError:
        pass


    # Test 10: Empty input.
    try:
        one_dimensional_k_cluster([], 1)
        assert False, "Expected ValueError"
    except ValueError:
        pass


    print("All tests passed.")


if __name__ == "__main__":
    run_tests()