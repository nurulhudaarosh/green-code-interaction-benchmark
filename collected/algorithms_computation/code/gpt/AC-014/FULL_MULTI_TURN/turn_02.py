"""
One-Dimensional K-Cluster Partition
===================================

Problem Restatement
-------------------
Given one-dimensional numeric points:

1. Sort the points in nondecreasing order.
2. Partition the sorted points into exactly k non-empty contiguous clusters.
3. The cost of a cluster is the sum of squared deviations of its points
   from that cluster's mean.
4. Minimize the total cost over all k clusters.
5. Return exactly:
       {
           "cost": minimum total cost,
           "boundaries": final boundary indices
       }

Boundary indices are zero-based inclusive ending indices in the sorted
array.

Deterministic Tie Rule
----------------------
If multiple valid partitions have the same minimum cost, choose the
partition whose split decision uses the smallest possible split index at
each DP state.

The implementation must use:
- prefix sums,
- prefix sums of squares,
- O(1) interval-cost calculation,
- interval-cost dynamic programming.

No unrelated behavior is changed.


Bug Demonstration
-----------------
A common defect is to use only:

    if candidate < best_cost:

without explicitly handling equal-cost candidates.

Consider:

    points = [0, 2, 4]
    k = 2

There are two optimal partitions:

    split = 1:
        [0] | [2, 4]
        cost = 0 + ((2-3)^2 + (4-3)^2) = 2

    split = 2:
        [0, 2] | [4]
        cost = ((0-1)^2 + (2-1)^2) + 0 = 2

Both have exactly the same minimum cost.

If the implementation does not explicitly enforce the deterministic
tie rule, the selected partition can depend on the iteration/update
logic. For example, changing the transition loop to iterate from large
split indices to small split indices would produce the other optimal
partition unless ties are handled explicitly.

The correction below therefore compares both cost and split index:

    if candidate < best_cost:
        ...
    elif candidate == best_cost and split < best_split:
        ...

Thus equal-cost choices always select the smaller split index.


Corrected Implementation
------------------------
"""

from math import isclose


def one_dimensional_k_cluster(points, k):
    """
    Partition one-dimensional points into exactly k non-empty contiguous
    clusters after sorting.

    Returns exactly:
        {
            "cost": minimum total cost,
            "boundaries": list of zero-based inclusive ending indices
        }

    Deterministic tie handling:
        For equal-cost DP transitions, the smaller split index is chosen.
    """

    n = len(points)

    if n == 0:
        raise ValueError("points must not be empty")

    if not 1 <= k <= n:
        raise ValueError("k must satisfy 1 <= k <= len(points)")

    # Sort the points as required.
    values = sorted(points)

    # Prefix sums and prefix sums of squares.
    prefix_sum = [0.0] * (n + 1)
    prefix_sq = [0.0] * (n + 1)

    for i, value in enumerate(values, start=1):
        x = float(value)
        prefix_sum[i] = prefix_sum[i - 1] + x
        prefix_sq[i] = prefix_sq[i - 1] + x * x

    def interval_cost(left, right):
        """
        Cost of the half-open interval [left, right).

        SSE = sum(x^2) - sum(x)^2 / count
        """
        count = right - left

        if count <= 0:
            return 0.0

        total = prefix_sum[right] - prefix_sum[left]
        total_sq = prefix_sq[right] - prefix_sq[left]

        cost = total_sq - (total * total) / count

        # Protect against tiny negative floating-point errors.
        if cost < 0.0 and abs(cost) < 1e-12:
            return 0.0

        return cost

    INF = float("inf")

    # dp[c][i] =
    # minimum cost for partitioning the first i sorted points
    # into exactly c non-empty clusters.
    dp = [[INF] * (n + 1) for _ in range(k + 1)]

    # parent[c][i] = split index producing dp[c][i].
    parent = [[-1] * (n + 1) for _ in range(k + 1)]

    dp[0][0] = 0.0

    # Interval-cost dynamic programming.
    for clusters in range(1, k + 1):
        for i in range(clusters, n + 1):

            best_cost = INF
            best_split = -1

            # Previous clusters use [0, split).
            # Current cluster uses [split, i).
            for split in range(clusters - 1, i):

                previous_cost = dp[clusters - 1][split]

                if previous_cost == INF:
                    continue

                candidate = (
                    previous_cost
                    + interval_cost(split, i)
                )

                # Primary rule: minimum cost.
                if candidate < best_cost:
                    best_cost = candidate
                    best_split = split

                # Deterministic tie rule:
                # equal cost -> smallest split index.
                elif candidate == best_cost:
                    if best_split == -1 or split < best_split:
                        best_split = split

            dp[clusters][i] = best_cost
            parent[clusters][i] = best_split

    # Reconstruct final boundaries.
    boundaries = []
    current_i = n

    for clusters in range(k, 0, -1):
        split = parent[clusters][current_i]

        if split == -1:
            raise RuntimeError("Failed to reconstruct clustering")

        # Current cluster is [split, current_i), so its final
        # zero-based inclusive index is current_i - 1.
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

    # --------------------------------------------------------
    # 1. Demonstrates the deterministic tie case.
    #
    # [0, 2, 4], k=2 has two optimal partitions:
    #
    # [0] | [2,4]       cost = 2
    # [0,2] | [4]       cost = 2
    #
    # Smaller split index = 1, so the required result is:
    # boundaries = [0, 2]
    # --------------------------------------------------------
    result = one_dimensional_k_cluster([0, 2, 4], 2)

    assert isclose(result["cost"], 2.0)
    assert result["boundaries"] == [0, 2]


    # --------------------------------------------------------
    # 2. Normal two-cluster case.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster([1, 2, 10, 11], 2)

    assert isclose(result["cost"], 1.0)
    assert result["boundaries"] == [1, 3]


    # --------------------------------------------------------
    # 3. Unsorted input must be sorted first.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster([11, 1, 10, 2], 2)

    assert isclose(result["cost"], 1.0)
    assert result["boundaries"] == [1, 3]


    # --------------------------------------------------------
    # 4. One cluster.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster([1, 2, 3], 1)

    assert isclose(result["cost"], 2.0)
    assert result["boundaries"] == [2]


    # --------------------------------------------------------
    # 5. k == n: every point is its own cluster.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster([5, 1, 3], 3)

    assert isclose(result["cost"], 0.0)
    assert result["boundaries"] == [0, 1, 2]


    # --------------------------------------------------------
    # 6. Repeated values.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [1, 1, 1, 10, 10, 10],
        2
    )

    assert isclose(result["cost"], 0.0)
    assert result["boundaries"] == [2, 5]


    # --------------------------------------------------------
    # 7. Negative values.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster([-5, -4, 10, 11], 2)

    assert isclose(result["cost"], 1.0)
    assert result["boundaries"] == [1, 3]


    # --------------------------------------------------------
    # 8. All values identical.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster([7, 7, 7, 7], 2)

    assert isclose(result["cost"], 0.0)
    assert len(result["boundaries"]) == 2


    # --------------------------------------------------------
    # 9. Invalid k.
    # --------------------------------------------------------
    try:
        one_dimensional_k_cluster([1, 2, 3], 0)
        assert False
    except ValueError:
        pass


    # --------------------------------------------------------
    # 10. Empty input.
    # --------------------------------------------------------
    try:
        one_dimensional_k_cluster([], 1)
        assert False
    except ValueError:
        pass


    print("All tests passed.")


if __name__ == "__main__":
    run_tests()