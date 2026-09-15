def min_squared_deviation_clustering(points: list[float], k: int) -> tuple[float, list[int]]:
    """
    Sorts 1D points and partitions them into k contiguous clusters 
    minimizing total sum of squared deviations from cluster means.
    
    Returns:
        (min_cost, boundary_indices)
    """
    n = len(points)
    if n == 0 or k <= 0:
        return 0.0, [0]
    
    # Sort points to ensure contiguous clustering property holds optimal solution
    arr = sorted(points)
    
    # Enforce k <= n (if k > n, each point gets its own cluster, cost is 0)
    k = min(k, n)
    
    # Precompute prefix sums for O(1) interval cost calculation
    P = [0.0] * (n + 1)   # Prefix sums of x
    Q = [0.0] * (n + 1)   # Prefix sums of x^2
    for i in range(n):
        P[i + 1] = P[i] + arr[i]
        Q[i + 1] = Q[i] + arr[i] * arr[i]
        
    def get_cost(i: int, j: int) -> float:
        """Returns SSE for subarray arr[i:j]."""
        count = j - i
        if count <= 0:
            return 0.0
        sum_x = P[j] - P[i]
        sum_x2 = Q[j] - Q[i]
        return sum_x2 - (sum_x * sum_x) / count

    # DP tables: dp[c][j] is the min cost for prefix of size j using c clusters
    dp = [[float('inf')] * (n + 1) for _ in range(k + 1)]
    parent = [[0] * (n + 1) for _ in range(k + 1)]
    
    # Base Case: 1 cluster for prefix of length j
    for j in range(1, n + 1):
        dp[1][j] = get_cost(0, j)
        parent[1][j] = 0
        
    # DP Transitions for c = 2..k
    for c in range(2, k + 1):
        for j in range(c, n + 1):
            for m in range(c - 1, j):
                cost = dp[c - 1][m] + get_cost(m, j)
                if cost < dp[c][j]:
                    dp[c][j] = cost
                    parent[c][j] = m

    # Backtrack boundaries
    boundaries = [0] * (k + 1)
    curr_j = n
    for c in range(k, 0, -1):
        boundaries[c] = curr_j
        curr_j = parent[c][curr_j]
    boundaries[0] = 0
    
    return dp[k][n], boundaries


# Example Execution:
if __name__ == "__main__":
    data = [2.0, 1.0, 10.0, 12.0, 3.0, 25.0, 28.0]
    k_clusters = 3
    
    cost, bounds = min_squared_deviation_clustering(data, k_clusters)
    sorted_data = sorted(data)
    
    print(f"Sorted Points: {sorted_data}")
    print(f"Minimum Cost: {cost:.4f}")
    print(f"Boundary Indices: {bounds}")
    
    # Print individual clusters
    for i in range(len(bounds) - 1):
        cluster = sorted_data[bounds[i]:bounds[i+1]]
        print(f" Cluster {i+1}: {cluster}")