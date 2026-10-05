"""
PROBLEM
    Given an m x n grid of non-negative costs, travel from the top-left cell
    (0, 0) to the bottom-right cell (m-1, n-1), moving only RIGHT or DOWN.
    The cost of a path is the sum of the costs of all cells visited,
    including the start and end cells.

KEY CONSTRAINTS
    - Grid is non-empty and rectangular (m >= 1, n >= 1).
    - All costs are non-negative numbers.
    - Moves: right (r, c+1) or down (r+1, c) only.
    - Standard library only; no network, randomness, or user interaction.
    - Output must be deterministic: same input -> same cost and same path.

REQUIRED OUTPUT
    (min_cost, path) where path is a list of (row, col) tuples from (0, 0)
    to (m-1, n-1), representing one optimal path.

ALGORITHM (dynamic programming with predecessors)
    dp[r][c] = grid[r][c] + min(dp[r-1][c], dp[r][c-1])
    Border cells have only one possible predecessor.
    For each cell store its predecessor coordinates.
    Tie rule: if coming from above and from the left cost the same, always
    choose ABOVE. This makes the reconstructed path unique and deterministic.
    Reconstruct by walking predecessors back from the goal, then reversing.
    Time O(m*n), space O(m*n).
"""

from typing import List, Optional, Sequence, Tuple

Cell = Tuple[int, int]


def min_cost_path(grid: Sequence[Sequence[float]]) -> Tuple[float, List[Cell]]:
    # ---- validation ----
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    m, n = len(grid), len(grid[0])
    for row in grid:
        if len(row) != n:
            raise ValueError("grid must be rectangular")
        for v in row:
            if v < 0:
                raise ValueError("costs must be non-negative")

    dp = [[0] * n for _ in range(m)]
    pred: List[List[Optional[Cell]]] = [[None] * n for _ in range(m)]

    # ---- fill DP table ----
    for r in range(m):
        for c in range(n):
            if r == 0 and c == 0:
                dp[r][c] = grid[r][c]
            elif r == 0:                      # first row: only from left
                dp[r][c] = dp[r][c - 1] + grid[r][c]
                pred[r][c] = (r, c - 1)
            elif c == 0:                      # first column: only from above
                dp[r][c] = dp[r - 1][c] + grid[r][c]
                pred[r][c] = (r - 1, c)
            else:
                up, left = dp[r - 1][c], dp[r][c - 1]
                if up <= left:                # deterministic tie: prefer above
                    dp[r][c] = up + grid[r][c]
                    pred[r][c] = (r - 1, c)
                else:
                    dp[r][c] = left + grid[r][c]
                    pred[r][c] = (r, c - 1)

    # ---- reconstruct path ----
    path: List[Cell] = []
    cur: Optional[Cell] = (m - 1, n - 1)
    while cur is not None:
        path.append(cur)
        cur = pred[cur[0]][cur[1]]
    path.reverse()

    return dp[m - 1][n - 1], path


if __name__ == "__main__":
    tests = [
        [[1, 3, 1], [1, 5, 1], [4, 2, 1]],   # expected cost 7
        [[5]],                               # single cell
        [[1, 2, 3]],                         # single row
        [[1], [2], [3]],                     # single column
        [[1, 1], [1, 1]],                    # tie -> deterministic (goes via above)
    ]
    for g in tests:
        cost, path = min_cost_path(g)
        print(f"grid={g}\n  min_cost={cost}\n  path={path}\n")