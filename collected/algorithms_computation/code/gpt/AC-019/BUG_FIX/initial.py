from typing import List, Tuple


def minimum_cost_path(
    cost: List[List[int]],
) -> Tuple[int, List[Tuple[int, int]]]:
    """
    Return the minimum cost and one deterministic optimal path.

    Movement is allowed only right or down.

    Tie-breaking rule:
        If moving from above and from the left gives the same cost,
        choose the cell from above.
    """

    if not cost or not cost[0]:
        raise ValueError("Cost matrix must not be empty.")

    rows = len(cost)
    cols = len(cost[0])

    # Validate that the matrix is rectangular and non-negative.
    for row in cost:
        if len(row) != cols:
            raise ValueError("Cost matrix must be rectangular.")
        if any(value < 0 for value in row):
            raise ValueError("All costs must be non-negative.")

    # dp[r][c] = minimum cost to reach (r, c)
    dp = [[0] * cols for _ in range(rows)]

    # parent[r][c] = predecessor coordinate
    parent = [[None] * cols for _ in range(rows)]

    # Starting cell
    dp[0][0] = cost[0][0]

    # First row: can only come from the left.
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + cost[0][c]
        parent[0][c] = (0, c - 1)

    # First column: can only come from above.
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + cost[r][0]
        parent[r][0] = (r - 1, 0)

    # Fill the remaining cells.
    for r in range(1, rows):
        for c in range(1, cols):
            from_above = dp[r - 1][c]
            from_left = dp[r][c - 1]

            # Deterministic tie-breaking:
            # choose ABOVE when costs are equal.
            if from_above <= from_left:
                dp[r][c] = from_above + cost[r][c]
                parent[r][c] = (r - 1, c)
            else:
                dp[r][c] = from_left + cost[r][c]
                parent[r][c] = (r, c - 1)

    # Reconstruct the path from bottom-right to top-left.
    path = []
    current = (rows - 1, cols - 1)

    while current is not None:
        path.append(current)
        r, c = current
        current = parent[r][c]

    # Reverse to obtain top-left -> bottom-right.
    path.reverse()

    return dp[rows - 1][cols - 1], path


# Example
if __name__ == "__main__":
    matrix = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1],
    ]

    minimum_cost, path = minimum_cost_path(matrix)

    print("Minimum cost:", minimum_cost)
    print("Path:", path)