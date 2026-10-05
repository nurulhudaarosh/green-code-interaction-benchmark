from typing import List, Tuple


def minimum_cost_path(
    cost: List[List[int]]
) -> Tuple[int, List[Tuple[int, int]]]:
    """
    Find a minimum-cost path from the top-left to the
    bottom-right of a non-negative cost matrix.

    Allowed moves:
        - Right
        - Down

    Tie handling:
        If coming from the top and left gives the same cost,
        choose the top predecessor.

    Returns:
        (minimum_cost, path)

    Example:
        >>> minimum_cost_path([
        ...     [1, 2, 3],
        ...     [4, 8, 2],
        ...     [1, 5, 3]
        ... ])
        (11, [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)])
    """

    # Validate the matrix
    if not cost or not cost[0]:
        raise ValueError("Cost matrix must be non-empty.")

    rows = len(cost)
    cols = len(cost[0])

    if any(len(row) != cols for row in cost):
        raise ValueError("Cost matrix must be rectangular.")

    if any(value < 0 for row in cost for value in row):
        raise ValueError("All costs must be non-negative.")

    # DP table
    dp = [[0] * cols for _ in range(rows)]

    # Parent/predecessor table
    parent = [[None] * cols for _ in range(rows)]

    # Starting cell
    dp[0][0] = cost[0][0]

    # First row: only possible predecessor is from the left
    for j in range(1, cols):
        dp[0][j] = dp[0][j - 1] + cost[0][j]
        parent[0][j] = (0, j - 1)

    # First column: only possible predecessor is from above
    for i in range(1, rows):
        dp[i][0] = dp[i - 1][0] + cost[i][0]
        parent[i][0] = (i - 1, 0)

    # Fill the remaining cells
    for i in range(1, rows):
        for j in range(1, cols):

            from_top = dp[i - 1][j]
            from_left = dp[i][j - 1]

            # Deterministic tie handling:
            # choose TOP when costs are equal.
            if from_top <= from_left:
                dp[i][j] = from_top + cost[i][j]
                parent[i][j] = (i - 1, j)
            else:
                dp[i][j] = from_left + cost[i][j]
                parent[i][j] = (i, j - 1)

    # Reconstruct the path
    path = []

    current = (rows - 1, cols - 1)

    while current is not None:
        path.append(current)

        i, j = current
        current = parent[i][j]

    # Currently the path is from destination to source
    path.reverse()

    return dp[rows - 1][cols - 1], path


# Example
if __name__ == "__main__":
    matrix = [
        [1, 2, 3],
        [4, 8, 2],
        [1, 5, 3]
    ]

    minimum_cost, path = minimum_cost_path(matrix)

    print("Minimum cost:", minimum_cost)
    print("Optimal path:", path)