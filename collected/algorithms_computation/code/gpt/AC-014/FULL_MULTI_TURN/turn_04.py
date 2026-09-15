"""
One-Dimensional K-Cluster Partition
===================================

Original Problem
----------------
Given one-dimensional numeric points:

1. Sort the points in nondecreasing order.
2. Partition the sorted points into exactly k non-empty contiguous clusters.
3. The cost of each cluster is the sum of squared deviations of its points
   from that cluster's mean.
4. Minimize the total cost across all k clusters.
5. Return:
       {
           "cost": minimum total clustering cost,
           "boundaries": final boundary indices
       }

Boundary indices are zero-based inclusive ending indices in the sorted array.

Algorithm
---------
Use prefix sums and prefix sums of squares so that the cost of any interval
can be calculated in O(1).

For a half-open interval [left, right):

    count = right - left
    sum_x = prefix_sum[right] - prefix_sum[left]
    sum_x2 = prefix_sq[right] - prefix_sq[left]

    cost = sum_x2 - (sum_x * sum_x) / count

Then use interval-cost dynamic programming:

    dp[c][i] =
        minimum cost for partitioning the first i sorted points
        into exactly c non-empty clusters.

Transition:

    dp[c][i] =
        min(
            dp[c-1][split] + interval_cost(split, i)
        )

where:

    c - 1 <= split < i

Deterministic Tie-Breaking
--------------------------
Repeated values can create multiple optimal partitions, and different
partitions can have exactly the same minimum cost.

The required deterministic rule is preserved:

    If two transitions have equal cost, choose the smaller split index.

This rule is explicitly implemented rather than relying on loop order.

Difficult Cases Handled
-----------------------
1. Repeated values:
   Example: [1, 1, 1, 10, 10, 10]

   Identical values can naturally form zero-cost clusters.

2. Deterministic ties:
   Example: [0, 2, 4], k=2

       [0] | [2,4] -> cost 2
       [0,2] | [4] -> cost 2

   Both are optimal. The smaller split index is selected, producing:

       boundaries = [0, 2]

3. All values identical.
4. Unsorted input.
5. Negative values.
6. k == 1.
7. k == n.

Output
------
The original output remains unchanged:

    {
        "cost": ...,
        "boundaries": [...]
    }

The optional operation_summary feature from the previous version is also
preserved. It is returned only when include_operation_summary=True.
"""


from math import isclose


def one_dimensional_k_cluster(
    points,
    k,
    include_operation_summary=False
):
    """
    Partition one-dimensional points into exactly k non-empty contiguous
    clusters after sorting.

    Returns:
        {
            "cost": minimum total clustering cost,
            "boundaries": zero-based inclusive ending indices
        }

    If include_operation_summary=True, also returns:
        "operation_summary": {
            "dp_transitions": number of evaluated DP transitions
        }

    Deterministic tie rule:
        Equal-cost transitions choose the smaller split index.
    """

    n = len(points)

    if n == 0:
        raise ValueError("points must not be empty")

    if not 1 <= k <= n:
        raise ValueError("k must satisfy 1 <= k <= len(points)")

    # --------------------------------------------------------
    # 1. Sort the points.
    # --------------------------------------------------------
    values = sorted(points)

    # --------------------------------------------------------
    # 2. Build prefix sums and prefix sums of squares.
    # --------------------------------------------------------
    prefix_sum = [0.0] * (n + 1)
    prefix_sq = [0.0] * (n + 1)

    for i, value in enumerate(values, start=1):
        x = float(value)

        prefix_sum[i] = prefix_sum[i - 1] + x
        prefix_sq[i] = prefix_sq[i - 1] + x * x

    # --------------------------------------------------------
    # 3. O(1) interval cost.
    # --------------------------------------------------------
    def interval_cost(left, right):
        """
        Cost for the half-open interval [left, right).
        """
        count = right - left

        if count <= 0:
            return 0.0

        total = prefix_sum[right] - prefix_sum[left]
        total_sq = prefix_sq[right] - prefix_sq[left]

        cost = total_sq - (total * total) / count

        # Prevent tiny negative values caused by floating-point
        # roundoff for theoretically zero-cost intervals.
        if cost < 0.0 and abs(cost) < 1e-12:
            cost = 0.0

        return cost

    INF = float("inf")

    # dp[c][i]:
    # first i sorted points, exactly c clusters.
    dp = [[INF] * (n + 1) for _ in range(k + 1)]

    # parent[c][i]:
    # split index that produced dp[c][i].
    parent = [[-1] * (n + 1) for _ in range(k + 1)]

    dp[0][0] = 0.0

    # Optional deterministic operation counter.
    dp_transitions = 0

    # --------------------------------------------------------
    # 4. Interval-cost dynamic programming.
    # --------------------------------------------------------
    for clusters in range(1, k + 1):
        for i in range(clusters, n + 1):

            best_cost = INF
            best_split = -1

            # Previous clusters: [0, split)
            # Current cluster:   [split, i)
            for split in range(clusters - 1, i):

                previous_cost = dp[clusters - 1][split]

                if previous_cost == INF:
                    continue

                dp_transitions += 1

                candidate = (
                    previous_cost
                    + interval_cost(split, i)
                )

                # Primary rule: smaller cost.
                if candidate < best_cost:
                    best_cost = candidate
                    best_split = split

                # Deterministic tie rule:
                # equal cost -> smaller split index.
                elif candidate == best_cost:
                    if best_split == -1 or split < best_split:
                        best_split = split

            dp[clusters][i] = best_cost
            parent[clusters][i] = best_split

    # --------------------------------------------------------
    # 5. Reconstruct final cluster boundaries.
    # --------------------------------------------------------
    boundaries = []
    current_i = n

    for clusters in range(k, 0, -1):

        split = parent[clusters][current_i]

        if split == -1:
            raise RuntimeError("Failed to reconstruct clustering")

        # Current cluster is [split, current_i).
        # Its inclusive ending index is current_i - 1.
        boundaries.append(current_i - 1)

        current_i = split

    boundaries.reverse()

    # --------------------------------------------------------
    # 6. Preserve the original output format.
    # --------------------------------------------------------
    result = {
        "cost": dp[k][n],
        "boundaries": boundaries,
    }

    if include_operation_summary:
        result["operation_summary"] = {
            "dp_transitions": dp_transitions
        }

    return result


# ============================================================
# Tests
# ============================================================

def run_tests():

    # --------------------------------------------------------
    # Test 1: Basic clustering.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [1, 2, 10, 11],
        2
    )

    assert isclose(result["cost"], 1.0)
    assert result["boundaries"] == [1, 3]


    # --------------------------------------------------------
    # Test 2: Repeated values.
    #
    # Sorted:
    #     [1, 1, 1, 10, 10, 10]
    #
    # Optimal:
    #     [1,1,1] | [10,10,10]
    #
    # Both clusters have zero variance.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [1, 10, 1, 10, 1, 10],
        2
    )

    assert isclose(result["cost"], 0.0)
    assert result["boundaries"] == [2, 5]


    # --------------------------------------------------------
    # Test 3: Repeated values with more clusters.
    #
    # [2,2,2,5,5,5], k=3
    #
    # A zero-cost partition exists. The deterministic DP rule
    # must still produce a stable answer.
    # --------------------------------------------------------
    result1 = one_dimensional_k_cluster(
        [2, 2, 2, 5, 5, 5],
        3
    )

    result2 = one_dimensional_k_cluster(
        [2, 2, 2, 5, 5, 5],
        3
    )

    assert isclose(result1["cost"], 0.0)
    assert result1 == result2
    assert len(result1["boundaries"]) == 3


    # --------------------------------------------------------
    # Test 4: Explicit deterministic tie.
    #
    # [0,2,4], k=2
    #
    # Split 1:
    #     [0] | [2,4] -> cost 2
    #
    # Split 2:
    #     [0,2] | [4] -> cost 2
    #
    # Equal cost => smaller split index wins.
    #
    # Therefore:
    #     boundaries = [0,2]
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [0, 2, 4],
        2
    )

    assert isclose(result["cost"], 2.0)
    assert result["boundaries"] == [0, 2]


    # --------------------------------------------------------
    # Test 5: Another deterministic tie with symmetric points.
    #
    # [-2, 0, 2], k=2
    #
    # Both possible split locations have the same total cost.
    # Smaller split index must win.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [-2, 0, 2],
        2
    )

    assert isclose(result["cost"], 2.0)
    assert result["boundaries"] == [0, 2]


    # --------------------------------------------------------
    # Test 6: Unsorted input.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [11, 1, 10, 2],
        2
    )

    assert isclose(result["cost"], 1.0)
    assert result["boundaries"] == [1, 3]


    # --------------------------------------------------------
    # Test 7: One cluster.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [1, 2, 3],
        1
    )

    assert isclose(result["cost"], 2.0)
    assert result["boundaries"] == [2]


    # --------------------------------------------------------
    # Test 8: Every point is its own cluster.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [5, 1, 3],
        3
    )

    assert isclose(result["cost"], 0.0)
    assert result["boundaries"] == [0, 1, 2]


    # --------------------------------------------------------
    # Test 9: Negative values.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [-5, -4, 10, 11],
        2
    )

    assert isclose(result["cost"], 1.0)
    assert result["boundaries"] == [1, 3]


    # --------------------------------------------------------
    # Test 10: All values identical.
    #
    # Every possible partition has zero total cost.
    # The DP tie rule makes the result deterministic.
    # --------------------------------------------------------
    result1 = one_dimensional_k_cluster(
        [7, 7, 7, 7],
        2
    )

    result2 = one_dimensional_k_cluster(
        [7, 7, 7, 7],
        2
    )

    assert isclose(result1["cost"], 0.0)
    assert result1 == result2
    assert result1["boundaries"] == [0, 3]


    # --------------------------------------------------------
    # Test 11: Original output is preserved when the optional
    # operation summary is disabled.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [1, 2, 10, 11],
        2,
        include_operation_summary=False
    )

    assert set(result.keys()) == {
        "cost",
        "boundaries"
    }


    # --------------------------------------------------------
    # Test 12: Optional operation summary remains available.
    # --------------------------------------------------------
    result = one_dimensional_k_cluster(
        [1, 2, 10, 11],
        2,
        include_operation_summary=True
    )

    assert set(result.keys()) == {
        "cost",
        "boundaries",
        "operation_summary"
    }

    assert result["operation_summary"]["dp_transitions"] == 9


    # --------------------------------------------------------
    # Test 13: Invalid k.
    # --------------------------------------------------------
    try:
        one_dimensional_k_cluster([1, 2, 3], 0)
        assert False, "Expected ValueError"
    except ValueError:
        pass


    # --------------------------------------------------------
    # Test 14: k greater than number of points.
    # --------------------------------------------------------
    try:
        one_dimensional_k_cluster([1, 2, 3], 4)
        assert False, "Expected ValueError"
    except ValueError:
        pass


    # --------------------------------------------------------
    # Test 15: Empty input.
    # --------------------------------------------------------
    try:
        one_dimensional_k_cluster([], 1)
        assert False, "Expected ValueError"
    except ValueError:
        pass


    print("All tests passed.")


if __name__ == "__main__":
    run_tests()