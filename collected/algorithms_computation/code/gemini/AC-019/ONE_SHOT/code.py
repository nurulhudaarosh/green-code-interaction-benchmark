def min_cost_path(cost_matrix):
    """
    Finds the minimum cost path in a grid from top-left to bottom-right 
    moving only right or down.
    
    Tie-breaking rule: Prefers coming from UP over LEFT when costs are equal.
    
    :param cost_matrix: List[List[number]], m x n non-negative grid
    :return: Tuple[number, List[Tuple[int, int]]]: (min_cost, path)
    """
    if not cost_matrix or not cost_matrix[0]:
        return 0, []

    m = len(cost_matrix)
    n = len(cost_matrix[0])

    dp = [[0] * n for _ in range(m)]
    parent = [[None] * n for _ in range(m)]

    # Initialize starting point
    dp[0][0] = cost_matrix[0][0]

    # Initialize first row (can only come from the Left)
    for c in range(1, n):
        dp[0][c] = dp[0][c - 1] + cost_matrix[0][c]
        parent[0][c] = (0, c - 1)

    # Initialize first column (can only come from Up)
    for r in range(1, m):
        dp[r][0] = dp[r - 1][0] + cost_matrix[r][0]
        parent[r][0] = (r - 1, 0)

    # Fill the DP and parent tables for the rest of the grid
    for r in range(1, m):
        for c in range(1, n):
            cost_from_up = dp[r - 1][c]
            cost_from_left = dp[r][c - 1]

            # Deterministic tie-handling: prefer UP if cost_from_up <= cost_from_left
            if cost_from_up <= cost_from_left:
                dp[r][c] = cost_matrix[r][c] + cost_from_up
                parent[r][c] = (r - 1, c)
            else:
                dp[r][c] = cost_matrix[r][c] + cost_from_left
                parent[r][c] = (r, c - 1)

    # Reconstruct the optimal path by backtracking from bottom-right
    path = []
    curr = (m - 1, n - 1)
    while curr is not None:
        path.append(curr)
        curr = parent[curr[0]][curr[1]]

    path.reverse()
    min_cost = dp[m - 1][n - 1]

    return min_cost, path


# Example usage:
if __name__ == "__main__":
    grid = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]
    min_cost, optimal_path = min_cost_path(grid)
    print(f"Minimum Cost: {min_cost}")
    print(f"Optimal Path: {optimal_path}")