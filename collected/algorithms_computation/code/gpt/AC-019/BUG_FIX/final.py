from typing import List, Tuple, Optional


def minimum_cost_path(
    cost: List[List[int]],
) -> Tuple[int, List[Tuple[int, int]]]:
    """
    Given a non-negative cost matrix, move only right or down
    from the top-left to the bottom-right.

    Returns exactly:
        (minimum_cost, path)

    Deterministic tie rule:
        If coming from above and from the left gives the same
        cost, choose the predecessor from above.
    """

    if not cost or not cost[0]:
        raise ValueError("Cost matrix must not be empty.")

    rows = len(cost)
    cols = len(cost[0])

    # Validate the matrix
    for row in cost:
        if len(row) != cols:
            raise ValueError("Cost matrix must be rectangular.")
        for value in row:
            if value < 0:
                raise ValueError("All costs must be non-negative.")

    # dp[r][c] = minimum cost to reach (r, c)
    dp = [[0] * cols for _ in range(rows)]

    # predecessor[r][c] = previous coordinate on the chosen path
    predecessor: List[List[Optional[Tuple[int, int]]]] = [
        [None] * cols for _ in range(rows)
    ]

    # Starting cell
    dp[0][0] = cost[0][0]

    # First row: can only come from the left
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + cost[0][c]
        predecessor[0][c] = (0, c - 1)

    # First column: can only come from above
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + cost[r][0]
        predecessor[r][0] = (r - 1, 0)

    # Fill the DP table
    for r in range(1, rows):
        for c in range(1, cols):
            from_above = dp[r - 1][c]
            from_left = dp[r][c - 1]

            # Deterministic tie handling:
            # if equal, choose the predecessor from above.
            if from_above <= from_left:
                dp[r][c] = from_above + cost[r][c]
                predecessor[r][c] = (r - 1, c)
            else:
                dp[r][c] = from_left + cost[r][c]
                predecessor[r][c] = (r, c - 1)

    # Reconstruct the path from bottom-right to top-left
    path = []
    current: Optional[Tuple[int, int]] = (rows - 1, cols - 1)

    while current is not None:
        path.append(current)
        r, c = current
        current = predecessor[r][c]

    # Reverse to get top-left -> bottom-right
    path.reverse()

    return dp[rows - 1][cols - 1], path


# Example
matrix = [
    [1, 1],
    [1, 1],
]

print(minimum_cost_path(matrix))
# Output:
# (3, [(0, 0), (0, 1), (1, 1)])