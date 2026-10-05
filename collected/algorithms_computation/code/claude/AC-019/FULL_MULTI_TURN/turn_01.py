from typing import List, Optional, Sequence, Tuple

Number = float  # ints work too; arithmetic is type-preserving


def min_cost_path(
    grid: Sequence[Sequence[Number]],
) -> Tuple[Number, List[Tuple[int, int]]]:
    """
    Return (minimum_cost, path) for moving only right/down from the
    top-left to the bottom-right of a non-negative cost grid.

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
            if v != v or v < 0:  # rejects NaN and negatives
                raise ValueError("grid values must be non-negative")

    # ---- DP tables --------------------------------------------------
    dp: List[List[Number]] = [[0] * cols for _ in range(rows)]
    prev: List[List[Optional[Tuple[int, int]]]] = [
        [None] * cols for _ in range(rows)
    ]

    dp[0][0] = grid[0][0]

    # First row: can only come from the left.
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + grid[0][c]
        prev[0][c] = (0, c - 1)

    # First column: can only come from above.
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + grid[r][0]
        prev[r][0] = (r - 1, 0)

    # Interior cells.
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
    tests = [
        [[1, 3, 1],
         [1, 5, 1],
         [4, 2, 1]],          # classic example
        [[5]],                # single cell
        [[1, 2, 3]],          # single row
        [[1], [2], [3]],      # single column
        [[1, 1],
         [1, 1]],             # tie: prefers arriving from above
        [[0, 0, 0],
         [0, 0, 0]],          # all zeros
    ]
    for g in tests:
        cost, p = min_cost_path(g)
        print(f"grid={g}\n  min cost = {cost}\n  path     = {p}\n")