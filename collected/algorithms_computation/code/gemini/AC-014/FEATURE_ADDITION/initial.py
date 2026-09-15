def min_squared_deviation_clustering(points: list[float], k: int) -> tuple[float, list[int]]:
    """
    Sorts 1D points and partitions them into k contiguous clusters 
    minimizing total sum of squared deviations from cluster means.
    
    Returns:
        tuple[float, list[int]]: (minimum_cost, boundary_indices)
        where boundary_indices lists the end index (exclusive) of each cluster.
    """
    if not points or k <= 0:
        return 0.0, []
        
    # Step 1: Sort points
    x = sorted(points)
    n = len(x)
    k = min(k, n)  # Cannot have more clusters than points
    
    # Step 2: Compute Prefix Sums for O(1) interval cost calculations
    # P1[i] = sum(x[0...i-1]), P2[i] = sum(x[0...i-1]^2)
    P1 = [0.0] * (n + 1)
    P2 = [0.0] * (n + 1)
    for i in range(n):
        P1[i + 1] = P1[i] + x[i]
        P2[i + 1] = P2[i] + x[i] ** 2
        
    def get_cost(i: int, j: int) -> float:
        """Cost of cluster spanning x[i:j] (0-indexed, exclusive right bound)."""
        count = j - i
        if count <= 1:
            return 0.0
        sum_x = P1[j] - P1[i]
        sum_x2 = P2[j] - P2[i]
        return sum_x2 - (sum_x ** 2) / count

    # Step 3: Dynamic Programming
    # DP[c][j] = min cost to partition x[0:j] into c clusters
    inf = float('inf')
    dp = [[inf] * (n + 1) for _ in range(k + 1)]
    split = [[0] * (n + 1) for _ in range(k + 1)]
    
    # Base case: 1 cluster
    for j in range(1, n + 1):
        dp[1][j] = get_cost(0, j)
        split[1][j] = 0
        
    # Fill DP for 2 to k clusters
    for c in range(2, k + 1):
        for j in range(c, n + 1):
            for m in range(c - 1, j):
                cost = dp[c - 1][m] + get_cost(m, j)
                if cost < dp[c][j]:
                    dp[c][j] = cost
                    split[c][j] = m

    # Step 4: Reconstruction of boundary indices
    boundaries = []
    curr = n
    for c in range(k, 0, -1):
        boundaries.append(curr)
        curr = split[c][curr]
    boundaries.reverse()

    return dp[k][n], boundaries


# Example Usage:
if __name__ == "__main__":
    data = [2.0, 1.0, 10.0, 12.0, 3.0, 25.0, 27.0]
    num_clusters = 3
    
    cost, boundaries = min_squared_deviation_clustering(data, num_clusters)
    print(f"Sorted Data: {sorted(data)}")
    print(f"Minimum Cost: {cost:.4f}")
    print(f"Cluster Boundaries (End Indices): {boundaries}")