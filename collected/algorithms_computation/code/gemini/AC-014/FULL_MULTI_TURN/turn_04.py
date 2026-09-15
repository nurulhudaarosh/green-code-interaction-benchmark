def min_squared_deviation_clustering(
    points: list[float], 
    k: int, 
    return_summary: bool = False
) -> tuple:
    """
    Sorts 1D points and partitions them into k contiguous clusters minimizing 
    the sum of squared deviations from cluster means, with deterministic tie handling.
    
    Args:
        points: List of 1D numerical values.
        k: Desired number of clusters.
        return_summary: If True, returns a 3-element tuple including an operation_summary dict.
        
    Returns:
        Default (return_summary=False): (cost, boundaries)
        Extended (return_summary=True):  (cost, boundaries, operation_summary)
    """
    n = len(points)
    if n == 0 or k <= 0:
        summary = {
            "total_points": 0,
            "target_clusters": 0,
            "interval_evaluations": 0,
            "tie_resolutions": 0
        }
        return (0.0, [0], summary) if return_summary else (0.0, [0])
    
    # Sort points deterministically
    arr = sorted(points)
    k_eff = min(k, n)
    
    # Metrics tracking
    evaluations_count = 0
    ties_count = 0
    
    # Precompute prefix sums for O(1) interval cost calculation
    P = [0.0] * (n + 1)   # Prefix sum of x
    Q = [0.0] * (n + 1)   # Prefix sum of x^2
    for i in range(n):
        P[i + 1] = P[i] + arr[i]
        Q[i + 1] = Q[i] + arr[i] * arr[i]
        
    def get_cost(i: int, j: int) -> float:
        """Calculates sum of squared errors (SSE) for subarray arr[i:j]."""
        count = j - i
        if count <= 0:
            return 0.0
        sum_x = P[j] - P[i]
        sum_x2 = Q[j] - Q[i]
        val = sum_x2 - (sum_x * sum_x) / count
        # Handle numerical precision underflow
        return max(0.0, val)

    # DP tables: dp[c][j] is the min cost for prefix of size j using c clusters
    dp = [[float('inf')] * (n + 1) for _ in range(k_eff + 1)]
    parent = [[0] * (n + 1) for _ in range(k_eff + 1)]
    
    # Base Case: 1 cluster for prefix of length j
    for j in range(1, n + 1):
        dp[1][j] = get_cost(0, j)
        parent[1][j] = 0
        
    EPS = 1e-12  # Floating-point equality threshold for ties
        
    # DP Transitions for c = 2..k
    for c in range(2, k_eff + 1):
        for j in range(c, n + 1):
            best_cost = float('inf')
            best_m = c - 1
            
            for m in range(c - 1, j):
                evaluations_count += 1
                cost = dp[c - 1][m] + get_cost(m, j)
                
                # Deterministic tie-handling: prefer strictly smaller costs;
                # break float equality ties (within EPS) by preferring smallest split index m
                if cost < best_cost - EPS:
                    best_cost = cost
                    best_m = m
                elif abs(cost - best_cost) <= EPS:
                    ties_count += 1
                    if m < best_m:
                        best_cost = cost
                        best_m = m

            dp[c][j] = best_cost
            parent[c][j] = best_m

    # Backtrack boundary indices
    boundaries = [0] * (k_eff + 1)
    curr_j = n
    for c in range(k_eff, 0, -1):
        boundaries[c] = curr_j
        curr_j = parent[c][curr_j]
    boundaries[0] = 0
    
    cost = dp[k_eff][n]
    
    if return_summary:
        operation_summary = {
            "total_points": n,
            "target_clusters": k_eff,
            "interval_evaluations": evaluations_count,
            "tie_resolutions": ties_count
        }
        return cost, boundaries, operation_summary
    
    return cost, boundaries


# ==========================================
# Comprehensive Unit Test Suite
# ==========================================

def run_tests():
    print("Running 1D K-Cluster Partition Difficult Case Tests...\n")
    
    # Test 1: All identical values (Repeated Values & Multiple Zero-Cost Ties)
    pts1 = [5.0, 5.0, 5.0, 5.0, 5.0]
    cost1, bounds1 = min_squared_deviation_clustering(pts1, 3)
    assert abs(cost1 - 0.0) < 1e-9, f"Expected cost 0.0, got {cost1}"
    # Smallest split index tie breaking forces bounds to [0, 1, 2, 5]
    assert bounds1 == [0, 1, 2, 5], f"Expected bounds [0, 1, 2, 5], got {bounds1}"
    print("✔ Test 1 Passed: All identical points (Zero variance & Smallest index tie-break)")

    # Test 2: Symmetric repeated blocks (Deterministic tie-breaking on symmetric splits)
    pts2 = [1.0, 1.0, 10.0, 10.0]
    cost2, bounds2 = min_squared_deviation_clustering(pts2, 2)
    assert abs(cost2 - 0.0) < 1e-9, f"Expected cost 0.0, got {cost2}"
    assert bounds2 == [0, 2, 4], f"Expected bounds [0, 2, 4], got {bounds2}"
    print("✔ Test 2 Passed: Symmetric repeated blocks cleanly split")

    # Test 3: k > n (More clusters than points)
    pts3 = [3.0, 1.0, 2.0]
    cost3, bounds3 = min_squared_deviation_clustering(pts3, 5)
    assert abs(cost3 - 0.0) < 1e-9
    assert bounds3 == [0, 1, 2, 3], f"Expected bounds [0, 1, 2, 3], got {bounds3}"
    print("✔ Test 3 Passed: k > n gracefully capped to k = n")

    # Test 4: Floating-Point Precision Tie Resolution
    # Symmetrically placed points where splitting at index 1 vs 2 yields mathematically equal costs
    pts4 = [0.0, 1.0, 1.0, 2.0]
    cost4, bounds4, summary4 = min_squared_deviation_clustering(pts4, 2, return_summary=True)
    assert bounds4 == [0, 1, 4], f"Expected smallest index tie resolution [0, 1, 4], got {bounds4}"
    assert summary4["tie_resolutions"] > 0, "Expected tie resolutions to be detected"
    print("✔ Test 4 Passed: Floating-point precision tie handled deterministically")

    # Test 5: Negative numbers and mixed values
    pts5 = [-10.0, -8.0, 0.0, 2.0, 100.0]
    cost5, bounds5 = min_squared_deviation_clustering(pts5, 2)
    assert bounds5 == [0, 4, 5], f"Expected bounds [0, 4, 5], got {bounds5}"
    print("✔ Test 5 Passed: Negative and mixed values handled correctly")

    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    run_tests()