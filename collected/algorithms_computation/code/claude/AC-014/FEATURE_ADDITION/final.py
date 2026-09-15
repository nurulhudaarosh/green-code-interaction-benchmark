"""
One-Dimensional K-Cluster Partition
============================================================

Problem restated
-----------------
Given a list of one-dimensional points, sort them and partition the sorted
sequence into k contiguous clusters (segments) so as to minimize the total
within-cluster sum of squared deviations from each cluster's own mean:

    cost = sum over clusters c of  sum_{x in c} (x - mean(c))^2

Because points are 1D, the optimal k-way partition minimizing SSE is always
achievable by contiguous segments of the *sorted* array, so we sort first
and then choose k-1 cut points among the sorted values.

Key constraints
---------------
- n = number of points, k = number of desired clusters, with 1 <= k <= n.
- Clusters must be contiguous ranges of the sorted points (a cluster may
  not skip over a point belonging to a neighboring cluster).
- Every point belongs to exactly one cluster; no cluster may be empty
  (each of the k clusters gets at least one point).
- The algorithm must be deterministic: identical input always yields an
  identical output. No randomness, no network/API calls, no external
  libraries, no human interaction.

Required outputs (unchanged from the original task)
-----------------------------------------------------
- "sorted_points": the sorted input points
- "cost": the minimal total sum-of-squared-deviations (float)
- "boundaries": list of k+1 indices into sorted_points defining cluster i
  as sorted_points[boundaries[i]:boundaries[i+1]]
- "clusters": the actual list-of-lists of points per cluster

New optional feature
---------------------
- An additional, OPT-IN field "operation_summary" may be returned. It
  reports a deterministic count of the major computational decisions/
  operations performed by the dynamic program, namely:
    * "dp_cells_computed": number of dp[m][j] table cells evaluated
    * "candidate_comparisons": number of (m, j, i) candidate splits
       considered/compared while filling those cells
    * "tie_break_updates": number of times a strictly-better candidate
       replaced the current best (i.e., actual "best found" updates)
    * "boundary_reconstruction_steps": number of backward-walk steps used
       to reconstruct the boundaries from the DP choice table
  This field is only computed and attached when the caller explicitly
  requests it (via `include_operation_summary=True`). When the feature is
  disabled (the default), behavior, fields, and values are exactly as in
  the original implementation -- nothing is added, changed, or removed.

Algorithm (unchanged)
----------------------
1. Sort the points.
2. Build prefix sums S[i] = sum of first i sorted points, and prefix sums
   of squares Q[i] = sum of squares of first i sorted points, giving O(1)
   segment-cost queries via:
       cost(i, j) = sq_seg - (sum_seg^2) / n_seg
3. DP over "clusters used" and "prefix length covered":
       dp[m][j] = min cost partitioning first j sorted points into m
                  contiguous, non-empty clusters
       dp[m][j] = min over i < j of ( dp[m-1][i] + cost(i, j) )
   with a `choice[m][j]` table storing the arg-min split point (ties
   broken deterministically by keeping the first minimizer found).
4. The answer is dp[k][n]; boundaries reconstructed by walking `choice`
   backward from (k, n) to (0, 0).

Complexity: O(k * n^2) time, O(k * n) space.
"""

from typing import List, Tuple
import math


def _prefix_sums(sorted_points: List[float]) -> Tuple[List[float], List[float]]:
    n = len(sorted_points)
    S = [0.0] * (n + 1)
    Q = [0.0] * (n + 1)
    for idx, x in enumerate(sorted_points, start=1):
        S[idx] = S[idx - 1] + x
        Q[idx] = Q[idx - 1] + x * x
    return S, Q


def _segment_cost(S: List[float], Q: List[float], i: int, j: int) -> float:
    """SSE cost of sorted_points[i:j] using prefix sums S, Q."""
    n_seg = j - i
    if n_seg <= 0:
        return 0.0
    sum_seg = S[j] - S[i]
    sq_seg = Q[j] - Q[i]
    return sq_seg - (sum_seg * sum_seg) / n_seg


def optimal_1d_clustering(
    points: List[float],
    k: int,
    include_operation_summary: bool = False,
) -> dict:
    """
    Partition `points` into k contiguous clusters (after sorting) minimizing
    total sum-of-squared-deviations from each cluster's mean.

    Parameters
    ----------
    points : list of numbers to cluster
    k : number of contiguous clusters required
    include_operation_summary : if True, attach an extra "operation_summary"
        field reporting deterministic counts of major DP decisions/
        operations. If False (default), the return value is identical in
        shape and content to the original task's required output.

    Returns
    -------
    dict with keys:
        "sorted_points", "cost", "boundaries", "clusters"
        and, only if include_operation_summary=True:
        "operation_summary"
    """
    if not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer")
    n = len(points)
    if n == 0:
        raise ValueError("points must be non-empty")
    if k > n:
        raise ValueError("k cannot exceed the number of points")

    sorted_points = sorted(points)
    S, Q = _prefix_sums(sorted_points)

    INF = math.inf

    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    choice = [[-1] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0

    # Operation counters (only meaningful / used if summary requested,
    # but tracking them is cheap and does not alter DP results either way).
    dp_cells_computed = 0
    candidate_comparisons = 0
    tie_break_updates = 0

    for m in range(1, k + 1):
        for j in range(m, n + 1):
            dp_cells_computed += 1
            best_cost = INF
            best_i = -1
            for i in range(m - 1, j):
                prev = dp[m - 1][i]
                if prev == INF:
                    continue
                candidate_comparisons += 1
                total = prev + _segment_cost(S, Q, i, j)
                if total < best_cost:  # strict '<' => deterministic first-min tie-break
                    best_cost = total
                    best_i = i
                    tie_break_updates += 1
            dp[m][j] = best_cost
            choice[m][j] = best_i

    total_cost = dp[k][n]
    if total_cost == INF:
        raise RuntimeError("No valid partition found (unexpected).")

    # Reconstruct boundaries by walking `choice` backward from (k, n)
    boundaries = [0] * (k + 1)
    boundaries[k] = n
    m, j = k, n
    boundary_reconstruction_steps = 0
    while m > 0:
        i = choice[m][j]
        boundaries[m - 1] = i
        j = i
        m -= 1
        boundary_reconstruction_steps += 1
    boundaries[0] = 0

    clusters = [
        sorted_points[boundaries[c]:boundaries[c + 1]] for c in range(k)
    ]

    result = {
        "sorted_points": sorted_points,
        "cost": total_cost,
        "boundaries": boundaries,
        "clusters": clusters,
    }

    if include_operation_summary:
        result["operation_summary"] = {
            "dp_cells_computed": dp_cells_computed,
            "candidate_comparisons": candidate_comparisons,
            "tie_break_updates": tie_break_updates,
            "boundary_reconstruction_steps": boundary_reconstruction_steps,
            "total_major_operations": (
                dp_cells_computed
                + candidate_comparisons
                + tie_break_updates
                + boundary_reconstruction_steps
            ),
        }

    return result


if __name__ == "__main__":
    sample_points = [4, 4.2, 4.1, 100, 101, 102, 50, 51, 200]
    k_clusters = 4

    # 1) Original behavior: feature disabled, output unchanged.
    result_plain = optimal_1d_clustering(sample_points, k_clusters)
    print("=== Without operation_summary (original behavior) ===")
    print("Sorted points :", result_plain["sorted_points"])
    print("k             :", k_clusters)
    print("Min SSE cost  : {:.6f}".format(result_plain["cost"]))
    print("Boundaries    :", result_plain["boundaries"])
    print("Clusters      :")
    for idx, c in enumerate(result_plain["clusters"]):
        print(f"  Cluster {idx}: {c}")
    print("Has operation_summary field:", "operation_summary" in result_plain)

    print()

    # 2) New opt-in feature enabled.
    result_full = optimal_1d_clustering(
        sample_points, k_clusters, include_operation_summary=True
    )
    print("=== With operation_summary (feature enabled) ===")
    print("Min SSE cost  : {:.6f}".format(result_full["cost"]))
    print("Boundaries    :", result_full["boundaries"])
    print("Operation summary:", result_full["operation_summary"])