def min_cost_path(matrix):
    """
    Finds the minimum cost path in a grid moving only Right or Down,
    using deterministic tie-breaking (prefers Up over Left predecessor).
    
    Args:
        matrix (List[List[Union[int, float]]]): Non-empty 2D grid of non-negative costs.
        
    Returns:
        Tuple[Union[int, float], List[Tuple[int, int]]]: (minimum_cost, path)
    """
    if not matrix or not matrix[0]:
        return 0, []

    rows = len(matrix)
    cols = len(matrix[0])

    dp = [[0] * cols for _ in range(rows)]
    parent = [[None] * cols for _ in range(rows)]

    # Base case
    dp[0][0] = matrix[0][0]

    # Initialize first column
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + matrix[r][0]
        parent[r][0] = (r - 1, 0)

    # Initialize first row
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + matrix[0][c]
        parent[0][c] = (0, c - 1)

    # Fill DP table with explicit, consistent tie-breaking
    for r in range(1, rows):
        for c in range(1, cols):
            from_up = dp[r - 1][c]
            from_left = dp[r][c - 1]

            # Deterministic tie-handling rule: Prefer Up over Left when costs match
            if from_up <= from_left:
                dp[r][c] = matrix[r][c] + from_up
                parent[r][c] = (r - 1, c)
            else:
                dp[r][c] = matrix[r][c] + from_left
                parent[r][c] = (r, c - 1)

    # Backtrack from bottom-right to top-left
    path = []
    curr = (rows - 1, cols - 1)
    while curr is not None:
        path.append(curr)
        curr = parent[curr[0]][curr[1]]

    path.reverse()
    return dp[rows - 1][cols - 1], path