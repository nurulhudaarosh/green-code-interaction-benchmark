from typing import List, Optional, Tuple

Coord = Tuple[int, int]


def min_cost_path(grid: List[List[float]]) -> Tuple[float, List[Coord]]:
    """
    Return (minimum_cost, path) for moving only right or down from (0, 0)
    to (m-1, n-1).

    Tie rule: if arriving from above and from the left cost the same,
    the predecessor is the cell above. This makes the result deterministic.
    """
    # ---- Validation ----
    if not grid or not grid[0]:
        raise ValueError("grid must be a non-empty matrix")
    m, n = len(grid), len(grid[0])
    for row in grid:
        if len(row) != n:
            raise ValueError("grid must be rectangular")
        for v in row:
            if v < 0:
                raise ValueError("costs must be non-negative")

    # ---- DP tables ----
    dp: List[List[float]] = [[0] * n for _ in range(m)]
    prev: List[List[Optional[Coord]]] = [[None] * n for _ in range(m)]

    dp[0][0] = grid[0][0]

    # First row: can only arrive from the left.
    for c in range(1, n):
        dp[0][c] = dp[0][c - 1] + grid[0][c]
        prev[0][c] = (0, c - 1)

    # First column: can only arrive from above.
    for r in range(1, m):
        dp[r][0] = dp[r - 1][0] + grid[r][0]
        prev[r][0] = (r - 1, 0)

    # Interior cells.
    for r in range(1, m):
        for c in range(1, n):
            from_up = dp[r - 1][c]
            from_left = dp[r][c - 1]
            if from_up <= from_left:          # tie -> prefer "up"
                dp[r][c] = grid[r][c] + from_up
                prev[r][c] = (r - 1, c)
            else:
                dp[r][c] = grid[r][c] + from_left
                prev[r][c] = (r, c - 1)

    # ---- Path reconstruction ----
    path: List[Coord] = []
    cur: Optional[Coord] = (m - 1, n - 1)
    while cur is not None:
        path.append(cur)
        cur = prev[cur[0]][cur[1]]
    path.reverse()

    return dp[m - 1][n - 1], path


def main() -> None:
    tests = [
        [[1, 3, 1],
         [1, 5, 1],
         [4, 2, 1]],                     # classic example
        [[5]],                           # single cell
        [[1, 2, 3, 4]],                  # single row
        [[1], [2], [3]],                 # single column
        [[1, 1],
         [1, 1]],                        # tie case
        [[0, 0, 0],
         [0, 0, 0]],                     # all zeros
    ]
    for g in tests:
        cost, path = min_cost_path(g)
        print(f"grid={g}")
        print(f"  min cost = {cost}")
        print(f"  path     = {path}\n")


if __name__ == "__main__":
    main()