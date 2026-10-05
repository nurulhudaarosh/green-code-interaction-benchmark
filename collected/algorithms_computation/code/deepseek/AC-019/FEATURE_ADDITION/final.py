def min_cost_path(cost_matrix, include_operation_summary=False):
    """
    Find minimum cost path from top-left to bottom-right.
    Can only move right or down.

    Args:
        cost_matrix: 2D list of non-negative integers.
        include_operation_summary: If True, also return a deterministic
            operation summary dict. If False, behavior is identical to the
            original function (only (min_cost, path) is returned).

    Returns:
        If include_operation_summary is False:
            (min_cost, path)
        If include_operation_summary is True:
            (min_cost, path, operation_summary)
        where:
            min_cost           -> int
            path               -> list of (row, col) tuples
            operation_summary  -> dict with key "major_decisions" (int)
    """
    # ---- Empty / degenerate input ----
    if not cost_matrix or not cost_matrix[0]:
        min_cost = 0
        path = []
        if include_operation_summary:
            operation_summary = {"major_decisions": 0}
            return min_cost, path, operation_summary
        return min_cost, path

    rows = len(cost_matrix)
    cols = len(cost_matrix[0])

    dp = [[0] * cols for _ in range(rows)]
    predecessor = [[None] * cols for _ in range(rows)]

    # Counter for major computational decisions (two-way comparisons)
    major_decisions = 0

    dp[0][0] = cost_matrix[0][0]

    # First row: only one predecessor (left) -> no decision
    for j in range(1, cols):
        dp[0][j] = dp[0][j - 1] + cost_matrix[0][j]
        predecessor[0][j] = (0, j - 1)

    # First column: only one predecessor (above) -> no decision
    for i in range(1, rows):
        dp[i][0] = dp[i - 1][0] + cost_matrix[i][0]
        predecessor[i][0] = (i - 1, 0)

    # Interior cells: two candidates -> one major decision each
    for i in range(1, rows):
        for j in range(1, cols):
            from_above = dp[i - 1][j]
            from_left = dp[i][j - 1]

            # This is a major computational decision:
            # compare the two candidates and pick a predecessor.
            major_decisions += 1

            # Deterministic tie-breaking: prefer "from above" on equality.
            if from_above <= from_left:
                dp[i][j] = cost_matrix[i][j] + from_above
                predecessor[i][j] = (i - 1, j)
            else:
                dp[i][j] = cost_matrix[i][j] + from_left
                predecessor[i][j] = (i, j - 1)

    # Reconstruct path
    path = []
    current = (rows - 1, cols - 1)
    while current is not None:
        path.append(current)
        current = predecessor[current[0]][current[1]]
    path.reverse()

    min_cost = dp[rows - 1][cols - 1]

    # ---- Return value depends on the feature flag ----
    if include_operation_summary:
        operation_summary = {"major_decisions": major_decisions}
        return min_cost, path, operation_summary

    return min_cost, path


# ----------------------------------------------------------------------
# Demonstration
# ----------------------------------------------------------------------
def print_solution(cost_matrix, include_operation_summary=False):
    """Display the solution; optionally show the operation summary."""
    if include_operation_summary:
        min_cost, path, operation_summary = min_cost_path(
            cost_matrix, include_operation_summary=True
        )
    else:
        min_cost, path = min_cost_path(cost_matrix)

    print("Cost Matrix:")
    for row in cost_matrix:
        print("  ", row)

    print(f"\nMinimum Cost: {min_cost}")
    print(f"Path: {path}")

    if include_operation_summary:
        print(f"Operation Summary: {operation_summary}")

    # Visualize
    print("\nPath visualization (X marks the path):")
    path_set = set(path)
    for i in range(len(cost_matrix)):
        row_str = "  "
        for j in range(len(cost_matrix[0])):
            if (i, j) in path_set:
                row_str += f"[{cost_matrix[i][j]}]"
            else:
                row_str += f" {cost_matrix[i][j]} "
            if j < len(cost_matrix[0]) - 1:
                row_str += " "
        print(row_str)


if __name__ == "__main__":
    print("=" * 60)
    print("Feature DISABLED -> original outputs only (min_cost, path)")
    print("=" * 60)
    m = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
    print_solution(m, include_operation_summary=False)

    print("\n" + "=" * 60)
    print("Feature ENABLED -> adds operation_summary")
    print("=" * 60)
    print_solution(m, include_operation_summary=True)

    print("\n" + "=" * 60)
    print("Consistency check across shapes")
    print("=" * 60)
    shapes = [
        ([[5]], "1x1"),
        ([[1, 2, 3, 4]], "1x4"),
        ([[1], [2], [3], [4]], "4x1"),
        ([[1, 1, 1], [1, 1, 1], [1, 1, 1]], "3x3 all ties"),
        ([[1, 2, 3, 4],
          [5, 6, 7, 8],
          [9, 10, 11, 12],
          [13, 14, 15, 16]], "4x4"),
    ]
    for matrix, label in shapes:
        mc, p, os_ = min_cost_path(matrix, include_operation_summary=True)
        expected = 0 if (len(matrix) == 0 or len(matrix[0]) == 0) \
            else (len(matrix) - 1) * (len(matrix[0]) - 1)
        ok = "OK" if os_["major_decisions"] == expected else "MISMATCH"
        print(f"  {label:10s} min_cost={mc:<4d} "
              f"major_decisions={os_['major_decisions']:<3d} "
              f"expected={expected:<3d} [{ok}]")