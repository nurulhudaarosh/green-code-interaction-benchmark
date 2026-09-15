"""
One-Dimensional K-Cluster Partition

Problem:
    Given one-dimensional points, sort them and partition the sorted points into
    exactly k contiguous, non-empty clusters. Minimize the sum of squared
    deviations of points from the mean of their own cluster.

    Return:
        - cost: minimum total sum of squared deviations
        - boundaries: final boundary indices of the clusters in the sorted array

Key constraints / requirements:
    - Points are one-dimensional numeric values.
    - Points are sorted before clustering.
    - Clusters must be contiguous in sorted order.
    - Exactly k non-empty clusters are required.
    - Cluster cost is the sum of squared deviations from that cluster's mean.
    - Use prefix sums to calculate interval costs efficiently.
    - Use interval-cost dynamic programming.
    - Tie handling is deterministic: when two choices have the same cost,
      choose the smaller boundary index.
    - No network, APIs, external services, randomness, or human interaction.
    - Standard library only.

Output:
    {
        "cost": minimum total squared deviation,
        "boundaries": [end_index_1, ..., end_index_k]
    }

    Boundary indices are zero-based and inclusive. For example:
        sorted points = [1, 2, 10, 11]
        boundaries = [1, 3]
    represents clusters [1, 2] and [10, 11].

Algorithm:
    1. Sort the input points.
    2. Build prefix sums:
           prefix_sum[i]  = sum of first i points
           prefix_sq[i]   = sum of squares of first i points
    3. For interval [left, right], calculate:
           cost = sum(x^2) - sum(x)^2 / count
       using the prefix sums.
    4. Let dp[c][i] be the minimum cost for partitioning the first i sorted
       points into exactly c clusters.
    5. Try every possible final cluster start position and use interval cost.
    6. Store the chosen boundary for reconstruction.
    7. Reconstruct the k cluster boundaries from the DP table.

Complexity:
    - Sorting: O(n log n)
    - DP: O(k * n^2)
    - Prefix-sum construction: O(n)
    - Memory: O(k * n)

Note:
    The implementation below uses exact integer arithmetic for the comparison
    whenever possible by representing each interval cost as:

        count * sum_of_squares - sum^2

    This is the original squared-deviation cost multiplied by `count`.
    Since cluster counts differ between candidate intervals, that scaled form
    cannot be summed directly across clusters. Therefore the DP uses Fraction
    from the standard library so that comparisons are exact and deterministic.
"""

from fractions import Fraction


def k_cluster_partition(points, k):
    """
    Partition one-dimensional points into exactly k contiguous clusters.

    Parameters
    ----------
    points : iterable of numbers
        One-dimensional input points.
    k : int
        Required number of non-empty clusters.

    Returns
    -------
    dict
        {
            "cost": minimum sum of squared deviations,
            "boundaries": zero-based inclusive end indices
        }

    Raises
    ------
    ValueError
        If k is invalid or more clusters than points are requested.
    """
    values = sorted(points)
    n = len(values)

    if k < 1:
        raise ValueError("k must be at least 1")

    if k > n:
        raise ValueError("k cannot exceed the number of points")

    # Prefix sums.
    prefix_sum = [0]
    prefix_sq = [0]

    for x in values:
        prefix_sum.append(prefix_sum[-1] + x)
        prefix_sq.append(prefix_sq[-1] + x * x)

    def interval_cost(left, right):
        """
        Cost of sorted values[left:right], where right is exclusive.

        SSE = sum(x^2) - sum(x)^2 / count
        """
        count = right - left
        total = prefix_sum[right] - prefix_sum[left]
        total_sq = prefix_sq[right] - prefix_sq[left]

        return Fraction(total_sq) - Fraction(total * total, count)

    # dp[c][i] = minimum cost for first i points using exactly c clusters.
    inf = None
    dp = [[inf] * (n + 1) for _ in range(k + 1)]

    # choice[c][i] = start index of the final cluster.
    choice = [[None] * (n + 1) for _ in range(k + 1)]

    dp[0][0] = Fraction(0)

    for clusters in range(1, k + 1):
        # Need at least `clusters` points for `clusters` non-empty clusters.
        for i in range(clusters, n + 1):
            best_cost = None
            best_start = None

            # Final cluster is [start, i).
            # The previous clusters occupy [0, start).
            for start in range(clusters - 1, i):
                previous = dp[clusters - 1][start]

                if previous is None:
                    continue

                candidate = previous + interval_cost(start, i)

                # Deterministic tie handling:
                # choose the smaller final-cluster start index.
                if (
                    best_cost is None
                    or candidate < best_cost
                    or (candidate == best_cost and start < best_start)
                ):
                    best_cost = candidate
                    best_start = start

            dp[clusters][i] = best_cost
            choice[clusters][i] = best_start

    # Reconstruct cluster boundaries.
    boundaries = []
    i = n

    for clusters in range(k, 0, -1):
        start = choice[clusters][i]

        if start is None:
            raise RuntimeError("Failed to reconstruct optimal partition")

        # The final cluster is [start, i), so its inclusive end is i - 1.
        boundaries.append(i - 1)
        i = start

    boundaries.reverse()

    # Convert an exact Fraction to int/float-friendly output.
    # For integer-valued costs, return an integer.
    final_cost = dp[k][n]
    if final_cost.denominator == 1:
        final_cost = final_cost.numerator
    else:
        final_cost = float(final_cost)

    return {
        "cost": final_cost,
        "boundaries": boundaries,
    }


# ------------------------------------------------------------
# Example
# ------------------------------------------------------------

if __name__ == "__main__":
    points = [1, 2, 10, 11]
    k = 2

    result = k_cluster_partition(points, k)

    print(result)
    # Expected:
    # {'cost': 1, 'boundaries': [1, 3]}

    # The sorted points are:
    # [1, 2, 10, 11]
    #
    # Cluster 1: [1, 2], mean = 1.5
    # Cost = (1 - 1.5)^2 + (2 - 1.5)^2 = 0.5
    #
    # Cluster 2: [10, 11], mean = 10.5
    # Cost = (10 - 10.5)^2 + (11 - 10.5)^2 = 0.5
    #
    # Total cost = 1.0