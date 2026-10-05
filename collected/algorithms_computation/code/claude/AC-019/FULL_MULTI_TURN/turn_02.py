import math
from typing import List, Optional, Sequence, Tuple

Number = float  # ints work too; arithmetic is type-preserving


def min_cost_path(
    grid: Sequence[Sequence[Number]],
) -> Tuple[Number, List[Tuple[int, int]]]:
    """
    Return (minimum_cost, path) for moving only right/down from the
    top-left to the bottom-right of a non-negative, finite cost grid.

    Tie rule: if arriving from above and from the left cost the same,
    the predecessor is the cell above ("up" is preferred).
    """
    # ---- Validation -------------------------------------------------
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    rows, cols = len(grid), len(grid[0])
    for row in grid:
        if len(row) != cols:
            raise ValueError("grid must be rectangular")
        for v in row:
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ValueError("grid values must be numbers")
            if not math.isfinite(v):  # FIX: rejects NaN, +inf, -inf
                raise ValueError("grid values must be finite")
            if v < 0:
                raise ValueError("grid values must be non-negative")

    # ---- DP tables --------------------------------------------------
    dp: List[List[Number]] = [[0] * cols for _ in range(rows)]
    prev: List[List[Optional[Tuple[int, int]]]] = [
        [None] * cols for _ in range(rows)
    ]
    dp[0][0] = grid[0][0]

    for c in range(1, cols):  # first row: only from the left
        dp[0][c] = dp[0][c - 1] + grid[0][c]
        prev[0][c] = (0, c - 1)

    for r in range(1, rows):  # first column: only from above
        dp[r][0] = dp[r - 1][0] + grid[r][0]
        prev[r][0] = (r - 1, 0)

    for r in range(1, rows):
        for c in range(1, cols):
            up, left = dp[r - 1][c], dp[r][c - 1]
            if up <= left:  # tie -> prefer up (deterministic)
                dp[r][c] = up + grid[r][c]
                prev[r][c] = (r - 1, c)
            else:
                dp[r][c] = left + grid[r][c]
                prev[r][c] = (r, c - 1)

    # ---- Path reconstruction ---------------------------------------
    path: List[Tuple[int, int]] = []
    cur: Optional[Tuple[int, int]] = (rows - 1, cols - 1)
    while cur is not None:
        path.append(cur)
        cur = prev[cur[0]][cur[1]]
    path.reverse()

    return dp[rows - 1][cols - 1], path


if __name__ == "__main__":
    # Classic grid: unique optimum, cost 7 (right, right, down, down).
    assert min_cost_path([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == (
        7, [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)])

    # Tie at (1,1): both routes cost 3; "up" predecessor is chosen.
    assert min_cost_path([[1, 1], [1, 1]]) == (3, [(0, 0), (0, 1), (1, 1)])

    # Tie at (1,1) with a later cell: path goes through (0,1), cost 5.
    assert min_cost_path([[1, 2, 3], [2, 1, 1]]) == (
        5, [(0, 0), (0, 1), (1, 1), (1, 2)])

    # Degenerate shapes.
    assert min_cost_path([[5]]) == (5, [(0, 0)])
    assert min_cost_path([[1, 2, 3]]) == (6, [(0, 0), (0, 1), (0, 2)])
    assert min_cost_path([[1], [2], [3]]) == (6, [(0, 0), (1, 0), (2, 0)])

    # Invalid inputs now all raise ValueError, including infinity.
    bad_inputs = [[], [[]], [[1, 2], [3]], [[-1]],
                  [[float("nan")]], [[float("inf")]], [[True]]]
    for bad in bad_inputs:
        try:
            min_cost_path(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")

    print("all checks passed")