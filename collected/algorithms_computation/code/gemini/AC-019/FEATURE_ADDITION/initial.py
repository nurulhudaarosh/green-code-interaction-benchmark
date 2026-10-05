def min_cost_path(cost):
    """
    Finds the minimum cost path in a grid moving only right or down.
    
    Args:
        cost (list[list[int | float]]): Non-negative cost matrix.
        
    Returns:
        tuple[int | float, list[tuple[int, int]]]: 
            - Minimum path cost
            - Deterministic optimal path as a list of (row, col) tuples.
    """
    if not cost or not cost[0]:
        return 0, []

    m, n = len(cost), len(cost[0])

    # dp[i][j] stores the min cost to reach cell (i, j)
    dp = [[0] * n for _ in range(m)]
    
    # parent[i][j] stores the predecessor tuple (r, c) for deterministic path reconstruction
    parent = [[None] * n for _ in range(m)]

    # Base case: Starting position
    dp[0][0] = cost[0][0]

    # Initialize first row (can only arrive from left)
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + cost[0][j]
        parent[0][j] = (0, j - 1)

    # Initialize first column (can only arrive from above)
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + cost[i][0]
        parent[i][0] = (i - 1, 0)

    # Fill DP table for remaining grid
    for i in range(1, m):
        for j in range(1, n):
            from_above = dp[i - 1][j]
            from_left = dp[i][j - 1]

            # Deterministic tie-handling: favor coming from left (Right move) on equality
            if from_left <= from_above:
                dp[i][j] = cost[i][j] + from_left
                parent[i][j] = (i, j - 1)
            else:
                dp[i][j] = cost[i][j] + from_above
                parent[i][j] = (i - 1, j)

    # Reconstruct optimal path backward from bottom-right to top-left
    path = []
    curr = (m - 1, n - 1)
    while curr is not None:
        path.append(curr)
        curr = parent[curr[0]][curr[1]]

    # Reverse to get path from (0, 0) to (m-1, n-1)
    path.reverse()

    return dp[m - 1][n - 1], path


# Example Usage & Verification
if __name__ == "__main__":
    grid = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]
    
    min_cost, path = min_cost_path(grid)
    print(f"Minimum Cost: {min_cost}")
    print(f"Path: {path}")