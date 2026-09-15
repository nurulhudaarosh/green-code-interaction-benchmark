"""
PROBLEM RESTATEMENT
--------------------
One-Dimensional K-Cluster Partition:
Given n real-valued points and an integer k, sort the points and partition
them into exactly k contiguous clusters (in sorted order) minimizing the
total within-cluster sum of squared deviations from each cluster's own mean.

EXISTING REQUIRED OUTPUTS (unchanged)
--------------------------------------
- total_cost: float, the minimized sum of squared deviations.
- boundaries: List[int] of length k+1, indices into the sorted point array
  marking cluster boundaries (boundaries[0] == 0, boundaries[-1] == n).
  Cluster i occupies sorted_points[boundaries[i]:boundaries[i+1]].

EXISTING REQUIRED CONSTRAINTS (unchanged)
-------------------------------------------
- Points sorted first; clusters must be contiguous in sorted order.
- Exact solution via prefix sums + interval-cost dynamic programming,
  O(k*n^2) time.
- Deterministic tie handling: among split points achieving the same minimal
  DP cost (within a small floating-point tolerance), the LARGEST tied split
  index is always chosen, regardless of floating-point summation noise.
- Standard library only; no randomness, no network/API calls, no external
  services, no human interaction.

NEW FEATURE (additive, opt-in)
--------------------------------
When requested (via `include_summary=True`), the function returns an
additional third field, `operation_summary`, alongside the two original
fields — a deterministic dict reporting the number of major computational
"decisions"/operations the DP made, specifically:
  - "interval_cost_evaluations": total number of O(1) interval_cost(i, j)
    calls performed (one per (c, j, i) candidate scanned).
  - "dp_states_filled": total number of dp[c][j] table cells computed
    (i.e. number of (c, j) states).
  - "tie_breaks_applied": number of times a genuine tie (within tolerance)
    was resolved by the deterministic "prefer larger i" rule.
  - "n_points": number of input points (n).
  - "k_clusters": number of clusters requested (k).

This is purely additive: when `include_summary` is False (the default) or
omitted, the return value is EXACTLY the original 2-tuple
(total_cost, boundaries), with no behavior change whatsoever. When True,
the return value becomes a 3-tuple
(total_cost, boundaries, operation_summary), with total_cost and boundaries
computed identically (same algorithm, same tie-break rule) — only the extra
summary is appended.
"""

from typing import List, Tuple, Union
import math


def cluster_1d(
    points: List[float],
    k: int,
    include_summary: bool = False,
) -> Union[Tuple[float, List[int]], Tuple[float, List[int], dict]]:
    """
    Partition 1-D points into k contiguous clusters minimizing the sum of
    squared deviations from each cluster's mean.

    Deterministic tie-break rule: among split points achieving the same
    minimal DP cost (compared within a small floating-point tolerance),
    the LARGEST split index is chosen.

    Args:
        points: list of real-valued points.
        k: number of contiguous clusters (1 <= k <= n).
        include_summary: if True, also return an `operation_summary` dict
            reporting deterministic counts of major DP operations. Default
            False preserves the original 2-tuple return signature exactly.

    Returns:
        If include_summary is False (default):
            (total_cost, boundaries)
        If include_summary is True:
            (total_cost, boundaries, operation_summary)
        where:
          - total_cost: float, minimized sum of squared deviations.
          - boundaries: List[int] of length k+1, cluster boundary indices
            into the sorted point array.
          - operation_summary: dict with keys
            "interval_cost_evaluations", "dp_states_filled",
            "tie_breaks_applied", "n_points", "k_clusters".
    """
    if not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer")
    n = len(points)
    if n == 0:
        raise ValueError("points must be non-empty")
    if k > n:
        raise ValueError("k cannot exceed the number of points")

    sorted_points = sorted(points)

    prefix_sum = [0.0] * (n + 1)
    prefix_sqsum = [0.0] * (n + 1)
    for idx in range(1, n + 1):
        v = sorted_points[idx - 1]
        prefix_sum[idx] = prefix_sum[idx - 1] + v
        prefix_sqsum[idx] = prefix_sqsum[idx - 1] + v * v

    def interval_cost(i: int, j: int) -> float:
        m = j - i
        if m <= 0:
            return 0.0
        s = prefix_sum[j] - prefix_sum[i]
        sq = prefix_sqsum[j] - prefix_sqsum[i]
        cost = sq - (s * s) / m
        return cost if cost > 0.0 else 0.0

    INF = math.inf
    TIE_EPS = 1e-9  # tolerance to treat near-equal floating costs as tied

    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    parent = [[-1] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0

    # Operation counters (deterministic bookkeeping, no effect on result)
    interval_cost_evaluations = 0
    dp_states_filled = 0
    tie_breaks_applied = 0

    for c in range(1, k + 1):
        for j in range(c, n + 1):
            best_cost = INF
            best_i = -1
            for i in range(c - 1, j):
                prev = dp[c - 1][i]
                if prev == INF:
                    continue
                total = prev + interval_cost(i, j)
                interval_cost_evaluations += 1
                if best_i == -1:
                    best_cost = total
                    best_i = i
                elif total < best_cost - TIE_EPS:
                    best_cost = total
                    best_i = i
                elif abs(total - best_cost) <= TIE_EPS:
                    tie_breaks_applied += 1
                    best_cost = total
                    best_i = i
                # else: strictly worse -> keep current best
            dp[c][j] = best_cost
            parent[c][j] = best_i
            dp_states_filled += 1

    total_cost = dp[k][n]
    if total_cost == INF:
        raise RuntimeError("No valid partition found (unexpected)")

    boundaries = [n]
    c, j = k, n
    while c > 0:
        i = parent[c][j]
        boundaries.append(i)
        j = i
        c -= 1
    boundaries.reverse()

    if not include_summary:
        # Original behavior, completely unchanged.
        return total_cost, boundaries

    operation_summary = {
        "interval_cost_evaluations": interval_cost_evaluations,
        "dp_states_filled": dp_states_filled,
        "tie_breaks_applied": tie_breaks_applied,
        "n_points": n,
        "k_clusters": k,
    }
    return total_cost, boundaries, operation_summary


if __name__ == "__main__":
    data = [0, 1, 2, 3]
    k = 2

    # Original call signature -> original 2-tuple, unaffected by the feature.
    cost, bounds = cluster_1d(data, k)
    print("Default (no summary):")
    print("  Total cost :", cost)
    print("  Boundaries :", bounds)

    print()

    # Opt-in call -> 3-tuple with operation_summary appended.
    cost2, bounds2, summary = cluster_1d(data, k, include_summary=True)
    print("With include_summary=True:")
    print("  Total cost        :", cost2)
    print("  Boundaries        :", bounds2)
    print("  Operation summary :", summary)
    assert cost == cost2 and bounds == bounds2, "core result must be identical"

    print()

    data2 = [1.0, 2.0, 3.0, 10.0, 11.0, 12.0, 25.0, 26.0, 100.0]
    k2 = 4
    cost3, bounds3, summary3 = cluster_1d(data2, k2, include_summary=True)
    sorted_data2 = sorted(data2)
    print("Larger example: k =", k2)
    print("  Total cost        :", cost3)
    print("  Boundaries        :", bounds3)
    print("  Operation summary :", summary3)
    for idx in range(len(bounds3) - 1):
        lo, hi = bounds3[idx], bounds3[idx + 1]
        print(f"    Cluster {idx}: {sorted_data2[lo:hi]}")