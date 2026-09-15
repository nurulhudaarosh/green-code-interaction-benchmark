from typing import List, Dict, Any, Tuple, Optional

def k_cluster_partition_1d(
    X: List[float], 
    K: int, 
    include_summary: bool = False
) -> Dict[str, Any]:
    """
    Partitions a sorted 1D array X into K contiguous clusters minimizing within-cluster SSE.
    
    :param X: Sorted list of numerical points.
    :param K: Number of clusters (1 <= K <= len(X)).
    :param include_summary: Optional flag to include operation_summary in the output.
    :return: Dictionary containing original outputs and optionally 'operation_summary'.
    """
    N = len(X)
    if N == 0 or K <= 0 or K > N:
        raise ValueError("Invalid parameters: Require 1 <= K <= N and non-empty X.")
    
    # Track deterministic operations
    op_count = 0
    
    # 1. Precompute prefix sums and prefix squared sums for O(1) interval cost lookup
    # P[i] = sum(X[0...i-1]), Q[i] = sum(X[0...i-1]^2)
    P = [0.0] * (N + 1)
    Q = [0.0] * (N + 1)
    for i in range(N):
        P[i + 1] = P[i] + X[i]
        Q[i + 1] = Q[i] + X[i] ** 2

    def get_cost(i: int, j: int) -> float:
        """Returns SSE for subarray X[i...j] in O(1) time."""
        nonlocal op_count
        op_count += 1
        count = j - i + 1
        s = P[j + 1] - P[i]
        sq_s = Q[j + 1] - Q[i]
        return sq_s - (s * s) / count

    # 2. Dynamic Programming Table Setup
    # dp[k][i] = min cost to partition X[0...i] into k clusters
    dp = [[float('inf')] * N for _ in range(K + 1)]
    parent = [[-1] * N for _ in range(K + 1)]

    # Base case: 1 cluster
    for i in range(N):
        dp[1][i] = get_cost(0, i)

    # DP Transitions
    for k in range(2, K + 1):
        for i in range(k - 1, N):
            for j in range(k - 1, i + 1):
                op_count += 1  # State decision operation evaluation
                cost = dp[k - 1][j - 1] + get_cost(j, i)
                if cost < dp[k][i]:
                    dp[k][i] = cost
                    parent[k][i] = j

    # 3. Backtrack to recover cluster boundaries
    clusters_bounds: List[Tuple[int, int]] = []
    curr_i = N - 1
    for k in range(K, 0, -1):
        if k == 1:
            clusters_bounds.append((0, curr_i))
        else:
            prev_split = parent[k][curr_i]
            clusters_bounds.append((prev_split, curr_i))
            curr_i = prev_split - 1

    clusters_bounds.reverse()

    # Build primary required output structures
    clusters = [X[start:end + 1] for start, end in clusters_bounds]
    centroids = [sum(cluster) / len(cluster) for cluster in clusters]
    total_cost = dp[K][N - 1]

    # Construct primary return dictionary
    result = {
        "clusters": clusters,
        "centroids": centroids,
        "total_cost": total_cost,
        "cluster_indices": clusters_bounds
    }

    # Add extended feature conditionally
    if include_summary:
        result["operation_summary"] = {
            "total_computational_operations": op_count,
            "complexity_order": "O(K * N^2)",
            "input_size_N": N,
            "target_clusters_K": K
        }

    return result