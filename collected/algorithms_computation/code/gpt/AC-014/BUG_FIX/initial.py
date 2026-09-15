"""
Problem Restatement
-------------------
Given a set of one-dimensional points, sort them and partition the sorted
points into exactly k contiguous, non-empty clusters.

For each cluster, its cost is the sum of squared deviations of its points
from that cluster's mean:

    cost(L, R) = sum((x[i] - mean(L, R))^2) for i in [L, R]

The goal is to minimize the total cost of all k clusters.

The solution must return:
1. The minimum total clustering cost.
2. The final boundary indices that describe the k contiguous clusters.

Key Constraints / Requirements
------------------------------
- Points are one-dimensional numeric values.
- Points are sorted before clustering.
- Clusters must be contiguous in sorted order.
- Exactly k non-empty clusters are required.
- The objective is the sum of squared deviations from each cluster mean.
- Use prefix sums to calculate interval costs efficiently.
- Use interval-cost dynamic programming to find the optimal partition.
- Tie-breaking is deterministic: when two partitions have the same cost,
  choose the one whose boundary-index list is lexicographically smaller.
- Use only Python's standard library.
- No network, APIs, external services, randomness, or human interaction.

Required Output
---------------
A dictionary containing:
    {
        "cost": minimum total clustering cost,
        "boundaries": final boundary indices
    }

Boundary convention:
- boundaries contains the ending index of each cluster in the sorted list.
- Indices are zero-based.
- For n points and k clusters, there are k boundary indices.
- The final boundary is always n - 1.

Example:
    sorted points = [1, 2, 3, 10, 11]
    boundaries = [2, 4]

means:
    cluster 1 -> indices 0..2
    cluster 2 -> indices 3..4


Algorithm
---------
1. Sort the points.
2. Build prefix sums:
       prefix_sum[i]
       prefix_square_sum[i]

3. For any interval [L, R], calculate:
       sum_x  = prefix_sum[R + 1] - prefix_sum[L]
       sum_x2 = prefix_square_sum[R + 1] - prefix_square_sum[L]
       count  = R - L + 1

   The squared-deviation cost can be computed as:
       sum_x2 - (sum_x * sum_x) / count

4. Define:
       dp[c][i] = minimum cost for partitioning the first i sorted points
                  into exactly c clusters.

   Transition:
       dp[c][i] = min(
           dp[c-1][j] + interval_cost(j, i-1)
       )

   where:
       c - 1 <= j < i

5. Store the corresponding boundary list for deterministic reconstruction.
   If two costs are equal, choose the lexicographically smaller boundary list.

Time Complexity
---------------
Sorting:              O(n log n)
Prefix sums:          O(n)
Dynamic programming:  O(k * n^2)
Space:                O(k * n)

The implementation below uses integer/rational-safe comparisons by using
the interval cost in the form:

    count * sum_x2 - sum_x^2

which is the usual variance cost multiplied by the interval size.

To return the actual sum of squared deviations, the DP stores costs as
Fractions. This keeps the result exact and deterministic even when means
are non-integers.
"""

from fractions import Fraction


def cluster_points(points, k):
    """
    Sort one-dimensional points and partition them into exactly k contiguous
    non-empty clusters minimizing the sum of squared deviations from each
    cluster mean.

    Returns:
        {
            "cost": exact minimum cost (int or Fraction),
            "boundaries": lexicographically smallest optimal boundary list
        }

    Raises:
        ValueError: if k is invalid or the input is empty when clustering
                    is requested.
    """

    n = len(points)

    if n == 0:
        if k == 0:
            return {
                "cost": 0,
                "boundaries": []
            }
        raise ValueError("Cannot create clusters from an empty point set.")

    if k < 1 or k > n:
        raise ValueError("k must satisfy 1 <= k <= number of points.")

    # Sort the points so every valid cluster is a contiguous interval.
    x = sorted(points)

    # Prefix sums of x and x^2.
    prefix_sum = [0] * (n + 1)
    prefix_square_sum = [0] * (n + 1)

    for i, value in enumerate(x):
        prefix_sum[i + 1] = prefix_sum[i] + value
        prefix_square_sum[i + 1] = prefix_square_sum[i] + value * value

    def interval_cost(left, right):
        """
        Exact sum of squared deviations from the interval mean for
        x[left:right+1].
        """
        count = right - left + 1

        total = prefix_sum[right + 1] - prefix_sum[left]
        total_square = (
            prefix_square_sum[right + 1] - prefix_square_sum[left]
        )

        # SSE = sum(x^2) - sum(x)^2 / count
        return Fraction(
            total_square * count - total * total,
            count
        )

    # dp_cost[c][i]:
    # minimum cost for the first i points using exactly c clusters.
    #
    # dp_boundaries[c][i]:
    # ending indices of those c clusters.
    dp_cost = [
        [None] * (n + 1)
        for _ in range(k + 1)
    ]

    dp_boundaries = [
        [None] * (n + 1)
        for _ in range(k + 1)
    ]

    dp_cost[0][0] = Fraction(0)
    dp_boundaries[0][0] = []

    for clusters in range(1, k + 1):
        # At least `clusters` points are necessary.
        for i in range(clusters, n + 1):
            best_cost = None
            best_boundaries = None

            # j = number of points assigned to previous clusters.
            # Current cluster is j .. i-1.
            for j in range(clusters - 1, i):
                previous_cost = dp_cost[clusters - 1][j]

                if previous_cost is None:
                    continue

                current_cost = (
                    previous_cost +
                    interval_cost(j, i - 1)
                )

                previous_boundaries = dp_boundaries[clusters - 1][j]

                # The boundary of the current cluster is i - 1.
                candidate_boundaries = (
                    previous_boundaries + [i - 1]
                )

                if best_cost is None:
                    best_cost = current_cost
                    best_boundaries = candidate_boundaries
                elif current_cost < best_cost:
                    best_cost = current_cost
                    best_boundaries = candidate_boundaries
                elif (
                    current_cost == best_cost
                    and candidate_boundaries < best_boundaries
                ):
                    # Deterministic tie-breaking.
                    best_boundaries = candidate_boundaries

            dp_cost[clusters][i] = best_cost
            dp_boundaries[clusters][i] = best_boundaries

    return {
        "cost": dp_cost[k][n],
        "boundaries": dp_boundaries[k][n]
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _run_tests():
    # Test 1: One cluster.
    result = cluster_points([1, 2, 3], 1)

    assert result["boundaries"] == [2]
    assert result["cost"] == Fraction(2)


    # Test 2: Two clearly separated clusters.
    result = cluster_points([1, 2, 10, 11], 2)

    assert result["boundaries"] == [1, 3]
    assert result["cost"] == Fraction(2)


    # Test 3: Input does not need to be pre-sorted.
    result = cluster_points([10, 1, 11, 2], 2)

    assert result["boundaries"] == [1, 3]
    assert result["cost"] == Fraction(2)


    # Test 4: Exactly n clusters means every point is its own cluster.
    result = cluster_points([5, 1, 9], 3)

    assert result["boundaries"] == [0, 1, 2]
    assert result["cost"] == Fraction(0)


    # Test 5: Smallest permitted input.
    result = cluster_points([42], 1)

    assert result["cost"] == 0
    assert result["boundaries"] == [0]


    # Test 6: Duplicate points.
    result = cluster_points([5, 5, 5, 5], 2)

    assert result["cost"] == 0
    assert result["boundaries"] == [0, 3]


    # Test 7: Non-integer mean.
    result = cluster_points([0, 1, 3], 1)

    # Mean = 4/3.
    # Cost = 0^2 + 1^2 + 3^2 - (4^2 / 3) = 14/3.
    assert result["cost"] == Fraction(14, 3)
    assert result["boundaries"] == [2]


    # Test 8: Negative values.
    result = cluster_points([-5, -4, 10, 11], 2)

    assert result["boundaries"] == [1, 3]
    assert result["cost"] == Fraction(2)


    # Test 9: Tie-breaking.
    #
    # [0, 2, 4] with two clusters:
    #
    # boundary [0, 2]:
    #   [0] and [2, 4] -> cost 2
    #
    # boundary [1, 2]:
    #   [0, 2] and [4] -> cost 2
    #
    # Both are optimal, so [0, 2] must be selected because it is
    # lexicographically smaller.
    result = cluster_points([0, 2, 4], 2)

    assert result["cost"] == Fraction(2)
    assert result["boundaries"] == [0, 2]


    # Test 10: Empty input with k = 0 is handled as an empty clustering.
    result = cluster_points([], 0)

    assert result["cost"] == 0
    assert result["boundaries"] == []


    # Test 11: Invalid empty input.
    try:
        cluster_points([], 1)
        assert False, "Expected ValueError"
    except ValueError:
        pass


    # Test 12: Invalid k.
    try:
        cluster_points([1, 2, 3], 4)
        assert False, "Expected ValueError"
    except ValueError:
        pass


    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()