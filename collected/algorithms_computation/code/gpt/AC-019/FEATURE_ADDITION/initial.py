def minimum_cost_grid_path(cost):
    """
    Return (minimum_cost, path) for a non-negative cost matrix.

    path is a list of (row, column) coordinates from (0, 0)
    to (rows - 1, cols - 1).

    Deterministic tie-breaking:
    When the top and left predecessors have equal cost,
    the top predecessor is chosen.
    """

    # Validate input
    if not cost or not cost[0]:
        raise ValueError("Cost matrix must be non-empty.")

    rows = len(cost)
    cols = len(cost[0])

    if any(len(row) != cols for row in cost):
        raise ValueError("Cost matrix must be rectangular.")

    if any(value < 0 for row in cost for value in row):
        raise ValueError("All costs must be non-negative.")

    # DP table and predecessor table
    dp = [[0] * cols for _ in range(rows)]
    parent = [[None] * cols for _ in range(rows)]

    # Starting cell
    dp[0][0] = cost[0][0]

    # First row: can only come from the left
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + cost[0][c]
        parent[0][c] = (0, c - 1)

    # First column: can only come from above
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + cost[r][0]
        parent[r][0] = (r - 1, 0)

    # Fill the DP table
    for r in range(1, rows):
        for c in range(1, cols):
            from_top = dp[r - 1][c]
            from_left = dp[r][c - 1]

            # Deterministic tie handling:
            # choose TOP when costs are equal.
            if from_top <= from_left:
                dp[r][c] = from_top + cost[r][c]
                parent[r][c] = (r - 1, c)
            else:
                dp[r][c] = from_left + cost[r][c]
                parent[r][c] = (r, c - 1)

    # Reconstruct the path by following predecessors
    path = []
    current = (rows - 1, cols - 1)

    while current is not None:
        path.append(current)
        r, c = current
        current = parent[r][c]

    path.reverse()

    return dp[rows - 1][cols - 1], path


# Example
if __name__ == "__main__":
    cost = [
        [1, 3, 1],
        [2, 2, 4],
        [5, 1, 1]
    ]

    minimum_cost, path = minimum_cost_grid_path(cost)

    print("Minimum cost:", minimum_cost)
    print("Path:", path)