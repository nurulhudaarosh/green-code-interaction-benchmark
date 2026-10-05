def min_cost_path(matrix):
    """
    Finds the minimum cost path in a grid moving only Right or Down.
    
    Args:
        matrix (List[List[int/float]]): Non-empty 2D grid of non-negative costs.
        
    Returns:
        Tuple[int/float, List[Tuple[int, int]]]: (minimum_cost, path_coordinates)
    """
    if not matrix or not matrix[0]:
        return 0, []

    rows = len(matrix)
    cols = len(matrix[0])

    dp = [[0] * cols for _ in range(rows)]
    parent = [[None] * cols for _ in range(rows)]

    # Base case: top-left corner
    dp[0][0] = matrix[0][0]

    # Initialize first column (can only come from above)
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + matrix[r][0]
        parent[r][0] = (r - 1, 0)

    # Initialize first row (can only come from the left)
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + matrix[0][c]
        parent[0][c] = (0, c - 1)

    # Fill the DP table
    for r in range(1, rows):
        for c in range(1, cols):
            from_up = dp[r - 1][c]
            from_left = dp[r][c - 1]

            # Deterministic tie-breaking: prefer Up over Left on equality
            if from_up <= from_left:
                dp[r][c] = matrix[r][c] + from_up
                parent[r][c] = (r - 1, c)
            else:
                dp[r][c] = matrix[r][c] + from_left
                parent[r][c] = (0, c) if r == 0 else (r, c - 1)

    # Backtrack to reconstruct the deterministic path
    path = []
    curr = (rows - 1, cols - 1)
    while curr is not None:
        path.append(curr)
        curr = parent[curr[0]][curr[1]]

    path.reverse()
    return dp[rows - 1][cols - 1], path


# --- Example Usage ---
if __name__ == "__main__":
    cost_matrix = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]

    min_cost, path = min_cost_path(cost_matrix)
    print(f"Minimum Cost: {min_cost}")
    print(f"Optimal Path: {path}")