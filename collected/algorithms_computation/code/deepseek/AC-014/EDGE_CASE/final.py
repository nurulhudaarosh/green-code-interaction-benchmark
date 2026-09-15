from typing import List, Tuple

EPS = 1e-9


def partition_points(points: List[float], k: int) -> Tuple[float, List[int]]:
    """
    Partition sorted 1D points into k contiguous clusters minimizing
    the sum of squared deviations from cluster means.

    Tie-breaking rules (deterministic):
      * Among equal-cost partitions, choose the one with lexicographically
        smallest boundaries.  Equivalently, on a DP tie pick the smallest i.
      * Costs are considered equal if |a - b| <= EPS = 1e-9.
      * Interval costs slightly below 0 (floating-point noise) are clamped to 0.

    Returns:
        (min_cost, boundaries)
        boundaries = [0, b1, ..., bk] with bk = n; cluster t is
        points[boundaries[t] : boundaries[t+1]].
    """
    n = len(points)
    if n == 0:
        return 0.0, [0]
    if k <= 0:
        raise ValueError("k must be positive")
    if k > n:
        raise ValueError("k cannot exceed number of points")

    # Prefix sums and prefix sums of squares
    P = [0.0] * (n + 1)
    Q = [0.0] * (n + 1)
    for i in range(n):
        P[i + 1] = P[i] + points[i]
        Q[i + 1] = Q[i] + points[i] * points[i]

    def interval_cost(i: int, j: int) -> float:
        """Cost of cluster points[i:j]. Clamped to >= 0 for FP safety."""
        m = j - i
        if m == 0:
            return 0.0
        s = P[j] - P[i]
        sq = Q[j] - Q[i]
        c = sq - (s * s) / m
        if c < 0.0 and c >= -EPS:
            return 0.0
        return c

    INF = float('inf')
    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    split = [[-1] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0

    for t in range(1, k + 1):
        for j in range(t, n + 1):
            best = INF
            best_i = -1
            for i in range(t - 1, j):
                if dp[t - 1][i] == INF:
                    continue
                cand = dp[t - 1][i] + interval_cost(i, j)
                # Tie-aware comparison: strictly better, OR equal within EPS
                # but with a smaller i (lexicographically earliest split).
                if cand < best - EPS:
                    best = cand
                    best_i = i
                elif abs(cand - best) <= EPS and i < best_i:
                    # Same cost, earlier split -> lexicographically smaller
                    best = min(best, cand)  # keep the smaller numeric value
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


# ----------------------------------------------------------------------
# Tests for the difficult cases
# ----------------------------------------------------------------------
def _wcss(points: List[float], bounds: List[int]) -> float:
    """Independent WCSS computation for verification."""
    total = 0.0
    for t in range(len(bounds) - 1):
        i, j = bounds[t], bounds[t + 1]
        cluster = points[i:j]
        m = len(cluster)
        if m == 0:
            continue
        mean = sum(cluster) / m
        total += sum((x - mean) ** 2 for x in cluster)
    return total


def test_repeated_values_cost_zero():
    """Repeated values: a cluster of identical points costs exactly 0."""
    points = [5.0, 5.0, 5.0, 5.0]
    cost, bounds = partition_points(points, 2)
    # Both clusters are all-5s -> total cost 0
    assert bounds == [0, 1, 4] or bounds == [0, 2, 4] or bounds == [0, 3, 4]
    assert cost == 0.0, f"expected 0.0, got {cost}"
    assert abs(_wcss(points, bounds)) <= EPS
    print("test_repeated_values_cost_zero: OK")


def test_repeated_values_tie_breaking():
    """
    All points identical -> every partition has cost 0. Lexicographically
    smallest boundaries should be chosen: [0, 1, 2, ..., n] for k < n
    is NOT lexicographically smallest; the smallest is [0, 1, 2, ...]
    only when k = n.  For k=2, n=4, lexicographically smallest valid
    boundary list is [0, 1, 4].
    """
    points = [7.0, 7.0, 7.0, 7.0]
    cost, bounds = partition_points(points, 2)
    assert bounds == [0, 1, 4], f"expected [0, 1, 4], got {bounds}"
    assert cost == 0.0
    print("test_repeated_values_tie_breaking: OK")


def test_repeated_values_full():
    """k = n: every point its own cluster, cost 0, boundaries = [0,1,...,n]."""
    points = [3.0, 3.0, 3.0, 3.0]
    cost, bounds = partition_points(points, 4)
    assert bounds == [0, 1, 2, 3, 4]
    assert cost == 0.0
    print("test_repeated_values_full: OK")


def test_tie_symmetric_gap():
    """
    [0, 1, 10, 11], k=2.  Two equally good splits:
      [0,1]|[10,11]  cost = 0.5 + 0.5 = 1.0
      [0]|[1,10,11]? -> not optimal
      [0,1,10]|[11]? -> not optimal
    The optimal split is [0,1] | [10,11] with cost 1.0.  Boundaries: [0,2,4].
    """
    points = [0.0, 1.0, 10.0, 11.0]
    cost, bounds = partition_points(points, 2)
    assert bounds == [0, 2, 4], f"got {bounds}"
    assert abs(cost - 1.0) <= EPS, f"got {cost}"
    print("test_tie_symmetric_gap: OK")


def test_tie_lexicographic_earliest():
    """
    Force a tie where two different i values give the same DP cost.
    points = [0, 1, 2, 3], k = 2.
      split at 1: [0] | [1,2,3]  cost = 0 + 2.0 = 2.0
      split at 2: [0,1] | [2,3]  cost = 0.5 + 0.5 = 1.0
      split at 3: [0,1,2] | [3]  cost = 2.0 + 0 = 2.0
    Not a tie.  Use points = [0, 2, 4, 6], k=2:
      split 2: [0,2]|[4,6] -> 2 + 2 = 4
      split 1: [0]|[2,4,6] -> 0 + 8 = 8
      split 3: [0,2,4]|[6] -> 8 + 0 = 8
    Minimum is 4 at i=2, unique.  To create a tie we use identical
    repeated values so every split costs 0 (covered above).
    Here we just verify the deterministic result for a symmetric case.
    """
    points = [0.0, 2.0, 4.0, 6.0]
    cost, bounds = partition_points(points, 2)
    assert bounds == [0, 2, 4]
    assert abs(cost - 4.0) <= EPS
    print("test_tie_lexicographic_earliest: OK")


def test_single_cluster_matches_variance():
    """k=1: cost should equal n * population variance."""
    points = [1.0, 2.0, 3.0, 10.0, 11.0, 12.0]
    cost, bounds = partition_points(points, 1)
    mean = sum(points) / len(points)
    expected = sum((x - mean) ** 2 for x in points)
    assert bounds == [0, len(points)]
    assert abs(cost - expected) <= EPS, f"{cost} vs {expected}"
    print("test_single_cluster_matches_variance: OK")


def test_k_equals_n_zero_cost():
    points = [1.0, 2.0, 3.0, 10.0, 11.0, 12.0]
    cost, bounds = partition_points(points, len(points))
    assert bounds == list(range(len(points) + 1))
    assert cost == 0.0
    print("test_k_equals_n_zero_cost: OK")


def test_repeated_with_outliers():
    """
    Mixed repeated values and outliers:
      [1,1,1, 1,1,1, 100]  k=2.
      Best split likely [1,1,1,1,1,1] | [100] -> cost 0 + 0 = 0.
      Boundaries [0,6,7].
    """
    points = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 100.0]
    cost, bounds = partition_points(points, 2)
    assert bounds == [0, 6, 7], f"got {bounds}"
    assert abs(cost) <= EPS, f"got {cost}"
    print("test_repeated_with_outliers: OK")


def test_negative_and_repeated():
    points = [-5.0, -5.0, -5.0, 5.0, 5.0, 5.0]
    cost, bounds = partition_points(points, 2)
    assert bounds == [0, 3, 6]
    assert abs(cost) <= EPS
    print("test_negative_and_repeated: OK")


def test_input_validation():
    try:
        partition_points([1.0, 2.0], 0)
        assert False, "expected ValueError for k=0"
    except ValueError:
        pass
    try:
        partition_points([1.0, 2.0], 5)
        assert False, "expected ValueError for k>n"
    except ValueError:
        pass
    cost, bounds = partition_points([], 1)
    assert cost == 0.0 and bounds == [0]
    print("test_input_validation: OK")


def run_all_tests():
    test_repeated_values_cost_zero()
    test_repeated_values_tie_breaking()
    test_repeated_values_full()
    test_tie_symmetric_gap()
    test_tie_lexicographic_earliest()
    test_single_cluster_matches_variance()
    test_k_equals_n_zero_cost()
    test_repeated_with_outliers()
    test_negative_and_repeated()
    test_input_validation()
    print("\nAll tests passed.")


def demo():
    points = [1.0, 2.0, 3.0, 10.0, 11.0, 12.0]
    k = 2
    cost, bounds = partition_points(points, k)
    print(f"Points: {points}")
    print(f"k = {k}")
    print(f"Minimum cost: {cost}")
    print(f"Boundaries: {bounds}")
    for c in range(len(bounds) - 1):
        i, j = bounds[c], bounds[c + 1]
        cluster = points[i:j]
        mean = sum(cluster) / len(cluster)
        print(f"  Cluster {c + 1}: {cluster} (mean={mean:.3f})")


if __name__ == "__main__":
    demo()
    print()
    run_all_tests()