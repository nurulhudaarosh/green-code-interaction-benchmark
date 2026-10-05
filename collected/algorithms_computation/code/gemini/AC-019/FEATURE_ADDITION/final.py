def min_cost_path(cost, return_summary=False):
    """
    Finds the minimum cost path in a grid moving only right or down.
    
    Args:
        cost (list[list[int | float]]): Non-negative cost matrix.
        return_summary (bool): If True, returns an additional operation summary.
        
    Returns:
        tuple[int | float, list[tuple[int, int]]] if return_summary is False
        tuple[int | float, list[tuple[int, int]], dict] if return_summary is True
    """
    if not cost or not cost[0]:
        summary = {
            "total_cells_processed": 0,
            "dp_cell_updates": 0,
            "min_decisions": 0,
            "path_step_count": 0,
        }
        return (0, [], summary) if return_summary else (0, [])

    m, n = len(cost), len(cost[0])

    dp = [[0] * n for _ in range(m)]
    parent = [[None] * n for _ in range(m)]

    # Tracking counters for operation summary
    total_cells = m * n
    dp_updates = 0
    min_decisions = 0

    # Base case: Starting position
    dp[0][0] = cost[0][0]
    dp_updates += 1

    # Initialize first row (can only arrive from left)
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + cost[0][j]
        parent[0][j] = (0, j - 1)
        dp_updates += 1

    # Initialize first column (can only arrive from above)
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + cost[i][0]
        parent[i][0] = (i - 1, 0)
        dp_updates += 1

    # Fill DP table for remaining grid
    for i in range(1, m):
        for j in range(1, n):
            from_above = dp[i - 1][j]
            from_left = dp[i][j - 1]

            # Binary choice decision (counted)
            min_decisions += 1

            # Deterministic tie-handling: favor coming from left (Right move) on equality
            if from_left <= from_above:
                dp[i][j] = cost[i][j] + from_left
                parent[i][j] = (i, j - 1)
            else:
                dp[i][j] = cost[i][j] + from_above
                parent[i][j] = (i - 1, j)

            dp_updates += 1

    # Reconstruct optimal path backward from bottom-right to top-left
    path = []
    curr = (m - 1, n - 1)
    while curr is not None:
        path.append(curr)
        curr = parent[curr[0]][curr[1]]

    path.reverse()
    min_cost = dp[m - 1][n - 1]

    if return_summary:
        operation_summary = {
            "total_cells_processed": total_cells,
            "dp_cell_updates": dp_updates,
            "min_decisions": min_decisions,
            "path_step_count": max(0, len(path) - 1),
        }
        return min_cost, path, operation_summary

    return min_cost, path


# Verification
if __name__ == "__main__":
    grid = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]

    # 1. Feature disabled (original requirements preserved)
    min_cost, path = min_cost_path(grid)
    print("Default Return:")
    print(f"  Cost: {min_cost}")
    print(f"  Path: {path}\n")

    # 2. Feature enabled (includes operation_summary)
    min_cost, path, summary = min_cost_path(grid, return_summary=True)
    print("Summary Return:")
    print(f"  Cost: {min_cost}")
    print(f"  Path: {path}")
    print(f"  Operation Summary: {summary}")