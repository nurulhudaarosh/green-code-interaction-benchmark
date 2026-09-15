def optimal_1d_k_means(points: list[float], k: int) -> tuple[float, list[int]]:
    """
    Sorts 1D points and partitions them into k contiguous clusters minimizing sum of squared errors.
    
    Deterministic tie handling: In case of equal costs, the smaller split index (m) is preferred.
    
    Returns:
        (min_cost, cluster_start_indices)
    """
    if not points or k <= 0:
        return 0.0, []
    
    # 1. Sort points deterministically
    sorted_pts = sorted(points)
    n = len(sorted_pts)
    
    # Edge case: k >= n. Every element forms its own cluster (cost = 0.0)
    if k >= n:
        # Return first n indices, pad remaining with n-1 to guarantee length k
        boundaries = list(range(n)) + [n - 1] * (k - n)
        return 0.0, boundaries
    
    # 2. Compute Prefix Sums (P1 for sum, P2 for sum of squares)
    P1 = [0.0] * (n + 1)
    P2 = [0.0] * (n + 1)
    for i in range(n):
        P1[i + 1] = P1[i] + sorted_pts[i]
        P2[i + 1] = P2[i] + sorted_pts[i] ** 2

    def get_cost(i: int, j: int) -> float:
        """Returns exact sum of squared deviations for sorted_pts[i:j+1]."""
        count = j - i + 1
        sum_x = P1[j + 1] - P1[i]
        sum_x2 = P2[j + 1] - P2[i]
        variance = sum_x2 - (sum_x * sum_x) / count
        return max(0.0, variance)

    # 3. Dynamic Programming Setup
    # dp[c][j] = min cost to partition first j points into c clusters
    dp = [[float('inf')] * (n + 1) for _ in range(k + 1)]
    split = [[0] * (n + 1) for _ in range(k + 1)]
    
    # Base Case: 1 cluster
    for j in range(1, n + 1):
        dp[1][j] = get_cost(0, j - 1)
        split[1][j] = 0

    # Fill DP table for 2 to k clusters
    EPS = 1e-12  # Numerical tolerance for deterministic tie handling
    
    for c in range(2, k + 1):
        for j in range(c, n + 1):
            best_cost = float('inf')
            best_m = c - 1
            
            for m in range(c - 1, j):
                cost = dp[c - 1][m] + get_cost(m, j - 1)
                
                # Deterministic tie-breaking: strict improvement considering float EPS
                if cost < best_cost - EPS:
                    best_cost = cost
                    best_m = m
                    
            dp[c][j] = max(0.0, best_cost)
            split[c][j] = best_m

    # 4. Backtrack boundary indices
    boundaries = [0] * k
    curr_j = n
    for c in range(k, 0, -1):
        boundaries[c - 1] = split[c][curr_j]
        curr_j = split[c][curr_j]

    final_cost = max(0.0, dp[k][n])
    return final_cost, boundaries