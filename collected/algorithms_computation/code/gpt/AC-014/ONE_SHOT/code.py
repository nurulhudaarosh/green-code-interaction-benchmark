"""
Problem: One-Dimensional Point Clustering

1. Problem Restatement
----------------------
Given a collection of one-dimensional points, sort the points and partition
them into exactly k contiguous clusters.

For every cluster, its cost is the sum of squared deviations of its points
from that cluster's mean:

    cost(cluster) = sum((x - mean(cluster)) ** 2)

The goal is to choose exactly k contiguous clusters after sorting so that the
total cost is minimized.

Return:
    - the minimum total clustering cost
    - the final boundary indices of the k clusters

Boundary representation:
    boundaries contains the 0-based ending index of every cluster in the
    sorted array. For example:

        sorted points = [1, 2, 3, 10, 11]
        boundaries = [2, 4]

    means clusters:
        [1, 2, 3]       -> indices 0..2
        [10, 11]        -> indices 3..4

    Thus the final boundary indices are [2, 4].

For deterministic tie handling, if multiple optimal partitions have the same
cost, the implementation prefers the partition with the smaller boundary
index at the earliest differing boundary.

2. Key Constraints
------------------
- Points are one-dimensional numeric values.
- Points are sorted before clustering.
- Exactly k non-empty contiguous clusters are required.
- 1 <= k <= n, where n is the number of points.
- The input contains no random or external dependencies.
- Only the Python standard library is used.
- The algorithm uses interval dynamic programming.
- Time complexity: O(k * n^2)
- Space complexity: O(k * n + n)

3. Required Output
------------------
Return a dictionary:

    {
        "cost": minimum_total_squared_deviation,
        "boundaries": [cluster_end_index_1, ..., cluster_end_index_k]
    }

The indices in "boundaries" refer to the sorted points and are 0-based.

For an empty input, there are no valid clusters, so k must also be 0.
In that case the result is:

    {
        "cost": 0.0,
        "boundaries": []
    }

4. Algorithm
-------------
Step 1:
    Sort the points.

Step 2:
    Build prefix sums:
        prefix_sum[i]  = sum of the first i points
        prefix_sq[i]   = sum of squares of the first i points

Step 3:
    For any interval [left, right], calculate its clustering cost in O(1):

        sum_x  = prefix_sum[right + 1] - prefix_sum[left]
        sum_x2 = prefix_sq[right + 1] - prefix_sq[left]
        length = right - left + 1

        cost = sum_x2 - (sum_x * sum_x) / length

Step 4:
    Use dynamic programming.

    dp[c][i] = minimum cost for partitioning the first i sorted points
               into exactly c non-empty clusters.

    If the last cluster starts at position j and ends at i - 1:

        dp[c][i] =
            min(
                dp[c-1][j] + interval_cost(j, i-1)
            )

    where:
        c - 1 <= j < i

Step 5:
    Store the chosen previous boundary for reconstruction.

Step 6:
    Reconstruct the cluster boundaries from dp[k][n].

Tie handling:
    When two candidates have equal cost, choose the smaller starting index
    of the final cluster. This produces deterministic boundaries and favors
    the lexicographically smaller boundary sequence.

5. Implementation
-----------------
"""

from typing import List, Sequence, Dict, Any


def cluster_1d(points: Sequence[float], k: int) -> Dict[str, Any]:
    """
    Sort one-dimensional points and partition them into exactly k contiguous
    clusters minimizing the sum of squared deviations from each cluster mean.

    Parameters
    ----------
    points:
        A sequence of numeric one-dimensional points.

    k:
        Number of required non-empty clusters.

    Returns
    -------
    dict
        {
            "cost": float,
            "boundaries": List[int]
        }

        boundaries contains the 0-based ending index of each cluster in the
        sorted point list.

    Raises
    ------
    ValueError
        If k is outside the valid range 0 <= k <= n, or if k == 0 while
        points are non-empty.
    """

    sorted_points = sorted(points)
    n = len(sorted_points)

    # Empty input is valid only with zero clusters.
    if n == 0:
        if k != 0:
            raise ValueError("For an empty input, k must be 0.")
        return {
            "cost": 0.0,
            "boundaries": [],
        }

    if not 1 <= k <= n:
        raise ValueError("k must satisfy 1 <= k <= number of points.")

    # Prefix sums and prefix sums of squares.
    prefix_sum = [0.0] * (n + 1)
    prefix_sq = [0.0] * (n + 1)

    for i, value in enumerate(sorted_points, start=1):
        x = float(value)
        prefix_sum[i] = prefix_sum[i - 1] + x
        prefix_sq[i] = prefix_sq[i - 1] + x * x

    def interval_cost(left: int, right: int) -> float:
        """
        Return the sum of squared deviations from the mean for the inclusive
        interval [left, right].
        """
        length = right - left + 1
        total = prefix_sum[right + 1] - prefix_sum[left]
        total_sq = prefix_sq[right + 1] - prefix_sq[left]

        cost = total_sq - (total * total) / length

        # Floating-point arithmetic can produce tiny negative values for
        # mathematically zero-cost intervals.
        if abs(cost) < 1e-12:
            return 0.0

        return cost

    # dp[c][i]:
    # minimum cost to partition the first i points into c clusters.
    #
    # Only two DP rows are needed for costs, while parent[c][i] stores the
    # starting index of the final cluster for reconstruction.
    inf = float("inf")

    dp_previous = [inf] * (n + 1)
    dp_previous[0] = 0.0

    parent = [[-1] * (n + 1) for _ in range(k + 1)]

    for clusters in range(1, k + 1):
        dp_current = [inf] * (n + 1)

        # At least `clusters` points are required for `clusters` non-empty
        # clusters.
        for i in range(clusters, n + 1):
            best_cost = inf
            best_start = -1

            # The final cluster starts at `start` and contains:
            # sorted_points[start:i]
            #
            # The previous clusters therefore cover:
            # sorted_points[0:start]
            for start in range(clusters - 1, i):
                previous_cost = dp_previous[start]

                if previous_cost == inf:
                    continue

                candidate = previous_cost + interval_cost(start, i - 1)

                # Deterministic tie handling:
                # choose the smaller starting index of the final cluster.
                if (
                    candidate < best_cost
                    or (
                        candidate == best_cost
                        and (best_start == -1 or start < best_start)
                    )
                ):
                    best_cost = candidate
                    best_start = start

            dp_current[i] = best_cost
            parent[clusters][i] = best_start

        dp_previous = dp_current

    minimum_cost = dp_previous[n]

    # Reconstruct cluster boundaries.
    boundaries = [0] * k
    end = n

    for clusters in range(k, 0, -1):
        start = parent[clusters][end]

        if start == -1:
            raise RuntimeError("Failed to reconstruct the optimal partition.")

        boundaries[clusters - 1] = end - 1
        end = start

    return {
        "cost": minimum_cost,
        "boundaries": boundaries,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _assert_close(actual: float, expected: float, eps: float = 1e-9) -> None:
    assert abs(actual - expected) <= eps, (
        f"Expected {expected}, got {actual}"
    )


def test_basic_two_clusters() -> None:
    points = [10, 1, 2, 11, 3]
    result = cluster_1d(points, 2)

    # Sorted: [1, 2, 3, 10, 11]
    #
    # Optimal partition:
    # [1, 2, 3] and [10, 11]
    #
    # First cluster cost = 2
    # Second cluster cost = 0.5
    # Total = 2.5
    _assert_close(result["cost"], 2.5)
    assert result["boundaries"] == [2, 4]


def test_k_equals_n() -> None:
    points = [5, 1, 9, 3]
    result = cluster_1d(points, 4)

    # Every point forms its own cluster, so every cluster has zero cost.
    _assert_close(result["cost"], 0.0)
    assert result["boundaries"] == [0, 1, 2, 3]


def test_one_cluster() -> None:
    points = [1, 2, 3, 4]
    result = cluster_1d(points, 1)

    # Mean = 2.5
    # Cost = 2.25 + 0.25 + 0.25 + 2.25 = 5
    _assert_close(result["cost"], 5.0)
    assert result["boundaries"] == [3]


def test_unsorted_input() -> None:
    points = [20, 2, 1, 21, 3, 22]
    result = cluster_1d(points, 2)

    # Sorted: [1, 2, 3, 20, 21, 22]
    # Optimal clusters: [1,2,3] and [20,21,22]
    # Each cluster has cost 2.
    _assert_close(result["cost"], 4.0)
    assert result["boundaries"] == [2, 5]


def test_duplicate_points() -> None:
    points = [5, 5, 5, 10, 10]
    result = cluster_1d(points, 2)

    # Both groups contain identical values, so total cost is zero.
    _assert_close(result["cost"], 0.0)

    # The deterministic DP chooses the earliest valid final-cluster start.
    assert result["boundaries"] == [2, 4]


def test_smallest_permitted_input() -> None:
    # Smallest non-empty case: one point and one cluster.
    points = [42]
    result = cluster_1d(points, 1)

    _assert_close(result["cost"], 0.0)
    assert result["boundaries"] == [0]


def test_empty_input() -> None:
    result = cluster_1d([], 0)

    assert result["cost"] == 0.0
    assert result["boundaries"] == []


def test_invalid_empty_input() -> None:
    try:
        cluster_1d([], 1)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for empty input with k=1.")


def test_invalid_k_zero_for_nonempty_input() -> None:
    try:
        cluster_1d([1, 2, 3], 0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for k=0 with non-empty input.")


def test_invalid_k_too_large() -> None:
    try:
        cluster_1d([1, 2, 3], 4)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for k > n.")


def test_negative_values() -> None:
    points = [-5, -4, -3, 10, 11]
    result = cluster_1d(points, 2)

    # [-5, -4, -3] has cost 2.
    # [10, 11] has cost 0.5.
    _assert_close(result["cost"], 2.5)
    assert result["boundaries"] == [2, 4]


def test_tie_is_deterministic() -> None:
    # All points are identical, so every possible partition has cost zero.
    # The deterministic tie rule chooses the earliest possible start for the
    # final cluster at every DP stage.
    points = [7, 7, 7, 7]
    result = cluster_1d(points, 2)

    _assert_close(result["cost"], 0.0)
    assert result["boundaries"] == [0, 3]


if __name__ == "__main__":
    test_basic_two_clusters()
    test_k_equals_n()
    test_one_cluster()
    test_unsorted_input()
    test_duplicate_points()
    test_smallest_permitted_input()
    test_empty_input()
    test_invalid_empty_input()
    test_invalid_k_zero_for_nonempty_input()
    test_invalid_k_too_large()
    test_negative_values()
    test_tie_is_deterministic()

    print("All tests passed.")