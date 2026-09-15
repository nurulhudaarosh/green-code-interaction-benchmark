from typing import List, Tuple

def min_ssd_1d_clustering(points: List[float], k: int) -> Tuple[float, List[int]]:
    """
    Sorts 1D points and partitions them into k optimal contiguous clusters.
    
    Returns:
        total_cost: The minimum sum of squared deviations from cluster means.
        boundaries: List of partition boundary indices (end indices of clusters).
    """
    n = len(points)
    if n == 0 or k <= 0:
        return 0.0, []
    
    # Step 1: Sort points
    sorted_x = sorted(points)
    
    if k >= n:
        # Every point is its own cluster; cost is 0.0
        return 0.0, list(range(1, n + 1))
    
    # Step 2: Build prefix sums for O(1) interval cost evaluation
    # P1[i] = sum(sorted_x[0:i]), P2[i] = sum(x^2 for x in sorted_x[0:i])
    P1 = [0.0] * (n + 1)
    P2 = [0.0] * (n + 1)
    for i in range(n):
        P1[i + 1] = P1[i] + sorted_x[i]
        P2[i + 1] = P2[i] + sorted_x[i] ** 2

    def cost(i: int, j: int) -> float:
        """Returns the SSD cost for sorted_x[i:j] (0-indexed, half-open interval)."""
        count = j - i
        if count <= 1:
            return 0.0
        sum_x = P1[j] - P1[i]
        sum_sq = P2[j] - P2[i]
        return max(0.0, sum_sq - (sum_x ** 2) / count)

    # Step 3: DP Table Initialization
    # dp[m][j]: min cost to cluster sorted_x[:j] into m clusters
    dp = [[float('inf')] * (n + 1) for _ in range(k + 1)]
    parent = [[0] * (n + 1) for _ in range(k + 1)]
    
    # Base case: 1 cluster
    for j in range(1, n + 1):
        dp[1][j] = cost(0, j)
        parent[1][j] = 0

    # Fill DP table for m = 2..k clusters
    for m in range(2, k + 1):
        for j in range(m, n + 1):
            for i in range(m - 1, j):
                current_cost = dp[m - 1][i] + cost(i, j)
                if current_cost < dp[m][j]:
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

# --- Example Usage ---
if __name__ == "__main__":
    data = [4.0, 1.0, 2.0, 10.0, 12.0, 3.0]
    num_clusters = 2
    
    cost_val, split_indices = min_ssd_1d_clustering(data, num_clusters)
    sorted_data = sorted(data)
    
    print(f"Sorted Data: {sorted_data}")
    print(f"Optimal Cost: {cost_val:.4f}")
    print(f"Cluster Boundaries (End Indices): {split_indices}")