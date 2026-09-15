def optimal_1d_k_means(points: list[float], k: int) -> tuple[float, list[int]]:
    """
    Sorts 1D points and partitions them into k contiguous clusters minimizing sum of squared errors.
    
    Returns:
        (min_cost, cluster_start_indices)
    """
    if not points or k <= 0:
        return 0.0, []
    
    # 1. Sort points
    sorted_pts = sorted(points)
    n = len(sorted_pts)
    
    # Edge case: more or equal clusters than points
    if k >= n:
        return 0.0, list(range(n))
    
    # 2. Compute Prefix Sums (P1 for linear sum, P2 for squared sum)
    P1 = [0.0] * (n + 1)
    P2 = [0.0] * (n + 1)
    for i in range(n):
        P1[i + 1] = P1[i] + sorted_pts[i]
        P2[i + 1] = P2[i] + sorted_pts[i] ** 2

    def get_cost(i: int, j: int) -> float:
        """Returns sum of squared deviations for sorted_pts[i:j+1]."""
        count = j - i + 1
        sum_x = P1[j + 1] - P1[i]
        sum_x2 = P2[j + 1] - P2[i]
        return max(0.0, sum_x2 - (sum_x * sum_x) / count)

    # 3. Dynamic Programming Setup
    # DP[c][j] = minimum cost using c clusters for the first j points
    dp = [[float('inf')] * (n + 1) for _ in range(k + 1)]
    split = [[0] * (n + 1) for _ in range(k + 1)]
    
    # Base Case: 1 cluster
    for j in range(1, n + 1):
        dp[1][j] = get_cost(0, j - 1)
        split[1][j] = 0

    # Fill DP for 2 to k clusters
    for c in range(2, k + 1):
        for j in range(c, n + 1):
            for m in range(c - 1, j):
                cost = dp[c - 1][m] + get_cost(m, j - 1)
                if cost < dp[c][j]:
                    dp[c][j] = cost
                    split[c][j] = m

    # 4. Backtrack boundary indices
    boundaries = [0] * k
    curr_j = n
    for c in range(k, 0, -1):
        boundaries[c - 1] = split[c][curr_j]
        curr_j = split[c][curr_j]

    return dp[k][n], boundaries


# --- Example Usage ---
if __name__ == "__main__":
    raw_points = [10.0, 2.0, 1.0, 12.0, 3.0, 20.0, 22.0]
    num_clusters = 3
    
    cost, boundary_indices = optimal_1d_k_means(raw_points, num_clusters)
    
    print(f"Sorted Points:     {sorted(raw_points)}")
    print(f"Minimal Cost:      {cost:.4f}")
    print(f"Boundary Indices:  {boundary_indices}")