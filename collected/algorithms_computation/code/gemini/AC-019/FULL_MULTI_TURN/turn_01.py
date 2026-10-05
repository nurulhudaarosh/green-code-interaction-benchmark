def min_path_cost(grid: list[list[int]]) -> tuple[int, list[tuple[int, int]]]:
    """
    Finds the minimum path cost and a deterministic optimal path 
    moving only right or down from top-left to bottom-right.
    """
    if not grid or not grid[0]:
        return 0, []

    m, n = len(grid), len(grid[0])
    
    # DP table to store minimum cumulative costs
    dp = [[0] * n for _ in range(m)]
    # Predecessor table to store parent coordinates for backtracking
    parent = [[None] * n for _ in range(m)]

    dp[0][0] = grid[0][0]

    # Initialize first row (can only come from the left)
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + grid[0][j]
        parent[0][j] = (0, j - 1)

    # Initialize first column (can only come from above)
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + grid[i][0]
        parent[i][0] = (i - 1, 0)

    # Fill the DP table
    for i in range(1, m):
        for j in range(1, n):
            from_up = dp[i - 1][j]
            from_left = dp[i][j - 1]

            # Deterministic tie-handling: prefer coming from UP over LEFT
            if from_up <= from_left:
                dp[i][j] = grid[i][j] + from_up
                parent[i][j] = (i - 1, j)
            else:
                dp[i][j] = grid[i][j] + from_left
                parent[i][j] = (i, j - 1)

    # Backtrack to reconstruct the optimal path
    path = []
    curr = (m - 1, n - 1)
    while curr is not None:
        path.append(curr)
        curr = parent[curr[0]][curr[1]]

    # Path is reconstructed from bottom-right to top-left, so reverse it
    path.reverse()

    return dp[m - 1][n - 1], path


# Example Execution:
if __name__ == "__main__":
    example_grid = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]

    min_cost, path = min_path_cost(example_grid)
    print("Minimum Cost:", min_cost)
    print("Deterministic Path:", path)