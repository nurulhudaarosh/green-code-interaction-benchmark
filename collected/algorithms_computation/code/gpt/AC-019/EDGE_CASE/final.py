def minimum_cost_grid_path(cost_matrix):
    """
    Minimum-Cost Grid Path

    Given a non-negative cost matrix, find a minimum-cost path from
    the top-left cell to the bottom-right cell.

    Allowed moves:
        - Right
        - Down

    Returns:
        {
            "minimum_cost": minimum_cost,
            "path": [(row, col), ...]
        }

    Deterministic tie-breaking:
        If moving from the top and left gives the same minimum cost,
        the top predecessor is always selected.
    """

    # -------------------------
    # Input validation
    # -------------------------
    if not cost_matrix:
        raise ValueError("cost_matrix must not be empty")

    if any(len(row) == 0 for row in cost_matrix):
        raise ValueError("cost_matrix must not contain empty rows")

    cols = len(cost_matrix[0])

    if any(len(row) != cols for row in cost_matrix):
        raise ValueError("cost_matrix must be rectangular")

    if any(cost < 0 for row in cost_matrix for cost in row):
        raise ValueError("All costs must be non-negative")

    rows = len(cost_matrix)

    # -------------------------
    # Dynamic Programming
    # -------------------------

    # dp[r][c] = minimum cost to reach (r, c)
    dp = [[0] * cols for _ in range(rows)]

    # parent[r][c] = predecessor coordinate
    parent = [[None] * cols for _ in range(rows)]

    # Starting cell
    dp[0][0] = cost_matrix[0][0]

    for r in range(rows):
        for c in range(cols):

            # Starting cell is already initialized
            if r == 0 and c == 0:
                continue

            from_top = float("inf")
            from_left = float("inf")

            if r > 0:
                from_top = dp[r - 1][c] + cost_matrix[r][c]

            if c > 0:
                from_left = dp[r][c - 1] + cost_matrix[r][c]

            # Deterministic tie handling:
            # top is preferred when costs are equal.
            if from_top <= from_left:
                dp[r][c] = from_top
                parent[r][c] = (r - 1, c)
            else:
                dp[r][c] = from_left
                parent[r][c] = (r, c - 1)

    # -------------------------
    # Reconstruct path
    # -------------------------

    path = []

    r = rows - 1
    c = cols - 1

    while True:
        path.append((r, c))

        if r == 0 and c == 0:
            break

        r, c = parent[r][c]

    path.reverse()

    return {
        "minimum_cost": dp[rows - 1][cols - 1],
        "path": path
    }


# ============================================================
# TESTS
# ============================================================

def run_tests():

    # --------------------------------------------------------
    # Test 1: Normal example
    # --------------------------------------------------------
    matrix = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]

    result = minimum_cost_grid_path(matrix)

    assert result == {
        "minimum_cost": 7,
        "path": [
            (0, 0),
            (1, 0),
            (2, 0),
            (2, 1),
            (2, 2)
        ]
    }

    # --------------------------------------------------------
    # Test 2: 1x1 boundary case
    # Only one cell exists.
    # --------------------------------------------------------
    matrix = [[42]]

    result = minimum_cost_grid_path(matrix)

    assert result == {
        "minimum_cost": 42,
        "path": [(0, 0)]
    }

    # --------------------------------------------------------
    # Test 3: Single row boundary case
    # Only right moves are possible.
    # --------------------------------------------------------
    matrix = [[1, 2, 3, 4, 5]]

    result = minimum_cost_grid_path(matrix)

    assert result == {
        "minimum_cost": 15,
        "path": [
            (0, 0),
            (0, 1),
            (0, 2),
            (0, 3),
            (0, 4)
        ]
    }

    # --------------------------------------------------------
    # Test 4: Single column boundary case
    # Only down moves are possible.
    # --------------------------------------------------------
    matrix = [
        [1],
        [2],
        [3],
        [4],
        [5]
    ]

    result = minimum_cost_grid_path(matrix)

    assert result == {
        "minimum_cost": 15,
        "path": [
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (4, 0)
        ]
    }

    # --------------------------------------------------------
    # Test 5: All-zero boundary values
    # Minimum cost must remain zero.
    # --------------------------------------------------------
    matrix = [
        [0, 0],
        [0, 0]
    ]

    result = minimum_cost_grid_path(matrix)

    # Both paths have equal cost.
    # Tie-breaking chooses TOP at (1,1).
    assert result == {
        "minimum_cost": 0,
        "path": [
            (0, 0),
            (0, 1),
            (1, 1)
        ]
    }

    # --------------------------------------------------------
    # Test 6: Explicit deterministic tie case
    # Both possible paths have equal cost.
    # At (1,1), top is preferred over left.
    # --------------------------------------------------------
    matrix = [
        [1, 1],
        [1, 1]
    ]

    result = minimum_cost_grid_path(matrix)

    assert result == {
        "minimum_cost": 3,
        "path": [
            (0, 0),
            (0, 1),
            (1, 1)
        ]
    }

    # --------------------------------------------------------
    # Test 7: Large boundary values
    # Use very large valid non-negative costs.
    # Python integers safely handle the resulting sum.
    # --------------------------------------------------------
    MAX_COST = 10**18

    matrix = [
        [MAX_COST, 1],
        [1, 1]
    ]

    result = minimum_cost_grid_path(matrix)

    assert result == {
        "minimum_cost": MAX_COST + 2,
        "path": [
            (0, 0),
            (1, 0),
            (1, 1)
        ]
    }

    # --------------------------------------------------------
    # Test 8: Large values with an optimal path
    # --------------------------------------------------------
    MAX_COST = 10**18

    matrix = [
        [MAX_COST, MAX_COST, MAX_COST],
        [1,        1,        MAX_COST],
        [MAX_COST, 1,        1]
    ]

    result = minimum_cost_grid_path(matrix)

    assert result == {
        "minimum_cost": MAX_COST + 4,
        "path": [
            (0, 0),
            (1, 0),
            (1, 1),
            (2, 1),
            (2, 2)
        ]
    }

    # --------------------------------------------------------
    # Test 9: Mixed zero and large boundary values
    # --------------------------------------------------------
    MAX_COST = 10**18

    matrix = [
        [0, MAX_COST, 0],
        [0, 0,       0],
        [MAX_COST, 0, 0]
    ]

    result = minimum_cost_grid_path(matrix)

    assert result == {
        "minimum_cost": 0,
        "path": [
            (0, 0),
            (1, 0),
            (1, 1),
            (1, 2),
            (2, 2)
        ]
    }

    # --------------------------------------------------------
    # Test 10: Invalid empty matrix
    # --------------------------------------------------------
    try:
        minimum_cost_grid_path([])
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # --------------------------------------------------------
    # Test 11: Invalid empty row
    # --------------------------------------------------------
    try:
        minimum_cost_grid_path([[]])
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # --------------------------------------------------------
    # Test 12: Invalid non-rectangular matrix
    # --------------------------------------------------------
    try:
        minimum_cost_grid_path([
            [1, 2],
            [3]
        ])
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # --------------------------------------------------------
    # Test 13: Invalid negative cost
    # --------------------------------------------------------
    try:
        minimum_cost_grid_path([
            [1, -1],
            [2, 3]
        ])
        assert False, "Expected ValueError"
    except ValueError:
        pass

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()