def minimum_cost_grid_path(cost, include_operation_summary=False):
    """
    Find a minimum-cost path from the top-left to the bottom-right
    of a non-negative cost matrix.

    Allowed moves:
        - Right
        - Down

    Deterministic tie-breaking:
        If the top and left predecessors have equal cost,
        choose the top predecessor.

    Original output:
        (minimum_cost, path)

    Extended output when include_operation_summary=True:
        (minimum_cost, path, operation_summary)
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

    # DP table:
    # dp[r][c] = minimum cost to reach (r, c)
    dp = [[0] * cols for _ in range(rows)]

    # Predecessor table:
    # parent[r][c] = coordinate used to reach (r, c)
    parent = [[None] * cols for _ in range(rows)]

    # Start cell
    dp[0][0] = cost[0][0]

    # Count major computational operations.
    # The start cell is not a decision, so it is not counted.
    operation_count = 0

    # First row: only possible predecessor is the left cell.
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + cost[0][c]
        parent[0][c] = (0, c - 1)
        operation_count += 1

    # First column: only possible predecessor is the cell above.
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + cost[r][0]
        parent[r][0] = (r - 1, 0)
        operation_count += 1

    # Fill the remaining DP cells.
    for r in range(1, rows):
        for c in range(1, cols):
            from_top = dp[r - 1][c]
            from_left = dp[r][c - 1]

            # Deterministic tie handling:
            # choose the top predecessor when equal.
            if from_top <= from_left:
                dp[r][c] = from_top + cost[r][c]
                parent[r][c] = (r - 1, c)
            else:
                dp[r][c] = from_left + cost[r][c]
                parent[r][c] = (r, c - 1)

            operation_count += 1

    # Reconstruct the path using predecessor coordinates.
    path = []
    current = (rows - 1, cols - 1)

    while current is not None:
        path.append(current)
        r, c = current
        current = parent[r][c]

    path.reverse()

    minimum_cost = dp[rows - 1][cols - 1]

    # Preserve the original output exactly when the feature
    # is not requested.
    if not include_operation_summary:
        return minimum_cost, path

    operation_summary = {
        "major_operations": operation_count
    }

    return minimum_cost, path, operation_summary


# Example: original behavior
cost = [
    [1, 3, 1],
    [2, 2, 4],
    [5, 1, 1]
]

result = minimum_cost_grid_path(cost)
print(result)

# Example: new feature requested
result_with_summary = minimum_cost_grid_path(
    cost,
    include_operation_summary=True
)
print(result_with_summary)