from typing import List, Tuple

def min_ssd_1d_clustering(points: List[float], k: int) -> Tuple[float, List[int]]:
    """
    Sorts 1D points and partitions them into k optimal contiguous clusters.
    
    Handles repeated values and deterministic tie-breaking stably.

    Returns:
        total_cost: The minimum sum of squared deviations from cluster means.
        boundaries: List of 1-based end indices for each cluster.
    """
    n = len(points)
    if n == 0 or k <= 0:
        return 0.0, []
    
    # Step 1: Sort points
    sorted_x = sorted(points)
    
    if k >= n:
        # Every point forms its own cluster; cost is 0.0
        return 0.0, list(range(1, n + 1))
    
    # Step 2: Prefix sums for O(1) interval cost computation
    P1 = [0.0] * (n + 1)
    P2 = [0.0] * (n + 1)
    for i in range(n):
        P1[i + 1] = P1[i] + sorted_x[i]
        P2[i + 1] = P2[i] + sorted_x[i] ** 2

    def cost(i: int, j: int) -> float:
        """Returns SSD cost for sorted_x[i:j] (0-indexed, half-open interval)."""
        count = j - i
        if count <= 1 or sorted_x[i] == sorted_x[j - 1]:
            return 0.0
        sum_x = P1[j] - P1[i]
        sum_sq = P2[j] - P2[i]
        val = sum_sq - (sum_x ** 2) / count
        return max(0.0, val)

    # Step 3: Dynamic Programming Table
    dp = [[float('inf')] * (n + 1) for _ in range(k + 1)]
    parent = [[0] * (n + 1) for _ in range(k + 1)]
    
    # Base case: m = 1 cluster
    for j in range(1, n + 1):
        dp[1][j] = cost(0, j)
        parent[1][j] = 0

    # Fill DP table for m = 2..k clusters
    eps = 1e-12
    for m in range(2, k + 1):
        for j in range(m, n + 1):
            for i in range(m - 1, j):
                current_cost = dp[m - 1][i] + cost(i, j)
                # Strict check with epsilon tolerance for deterministic tie-breaking
                if current_cost < dp[m][j] - eps:
                    dp[m][j] = current_cost
                    parent[m][j] = i

    # Step 4: Backtrack boundary indices
    boundaries = []
    curr_j = n
    for m in range(k, 0, -1):
        boundaries.append(curr_j)
        curr_j = parent[m][curr_j]
    
    boundaries.reverse()
    total_cost = dp[k][n]
    
    return total_cost, boundaries


# --- Unit Tests for Corner Cases & Ties ---
def run_tests():
    # Test 1: Repeated values
    data1 = [2.0, 2.0, 2.0, 5.0, 5.0, 5.0]
    cost1, bounds1 = min_ssd_1d_clustering(data1, 2)
    assert abs(cost1 - 0.0) < 1e-9, f"Expected 0 cost, got {cost1}"
    assert bounds1 == [3, 6], f"Expected boundaries [3, 6], got {bounds1}"

    # Test 2: Symmetric values with tie-breaking
    data2 = [1.0, 2.0, 8.0, 9.0]
    cost2, bounds2 = min_ssd_1d_clustering(data2, 2)
    expected_cost2 = 0.5 + 0.5  # ((1-1.5)^2 + (2-1.5)^2) + ((8-8.5)^2 + (9-8.5)^2)
    assert abs(cost2 - expected_cost2) < 1e-9, f"Expected {expected_cost2}, got {cost2}"
    assert bounds2 == [2, 4], f"Expected boundaries [2, 4], got {bounds2}"

    # Test 3: k >= n (Singletons)
    data3 = [10.0, 30.0, 20.0]
    cost3, bounds3 = min_ssd_1d_clustering(data3, 4)
    assert cost3 == 0.0, f"Expected 0 cost, got {cost3}"
    assert bounds3 == [1, 2, 3], f"Expected boundaries [1, 2, 3], got {bounds3}"

    # Test 4: All identical elements
    data4 = [7.0, 7.0, 7.0, 7.0]
    cost4, bounds4 = min_ssd_1d_clustering(data4, 2)
    assert abs(cost4 - 0.0) < 1e-9, f"Expected 0 cost, got {cost4}"
    assert len(bounds4) == 2 and bounds4[-1] == 4

    print("All unit tests passed successfully!")

if __name__ == "__main__":
    run_tests()