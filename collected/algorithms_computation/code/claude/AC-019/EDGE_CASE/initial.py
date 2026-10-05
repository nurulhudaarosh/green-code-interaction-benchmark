"""
PROBLEM
-------
Given a grid `cost` of non-negative numbers, start at the top-left cell (0, 0)
and reach the bottom-right cell (m-1, n-1) moving only RIGHT or DOWN.
The cost of a path is the sum of the cell costs it visits (both endpoints included).

KEY CONSTRAINTS
---------------
- Moves: right (r, c+1) or down (r+1, c) only.
- Costs are non-negative; grid is rectangular and non-empty.
- Standard library only; no network, randomness, or user interaction.
- Output must be deterministic: same input -> same cost and same path.

REQUIRED OUTPUT
---------------
(min_cost, path), where path is a list of (row, col) tuples from (0, 0) to
(m-1, n-1) describing ONE optimal path.

ALGORITHM (Dynamic Programming with predecessor tracking)
---------------------------------------------------------
dp[i][j] = cost[i][j] + min(dp[i-1][j], dp[i][j-1])   (only existing neighbors)
prev[i][j] stores the coordinates of the chosen predecessor.
Tie handling: if dp[i-1][j] == dp[i][j-1], ALWAYS choose the cell above
(i-1, j). Cells are processed in fixed row-major order, so the result is
fully deterministic. The path is rebuilt by walking prev[][] back from the
goal, then reversing. Time O(m*n), space O(m*n).
"""

from typing import List, Tuple, Sequence, Union

Number = Union[int, float]


def min_cost_path(cost: Sequence[Sequence[Number]]) -> Tuple[Number, List[Tuple[int, int]]]:
    # ---- validation ----
    if not cost or not cost[0]:
        raise ValueError("cost matrix must be non-empty")
    m, n = len(cost), len(cost[0])
    for row in cost:
        if len(row) != n:
            raise ValueError("cost matrix must be rectangular")
        for v in row:
            if v < 0:
                raise ValueError("costs must be non-negative")

    dp = [[0] * n for _ in range(m)]
    prev: List[List[Union[None, Tuple[int, int]]]] = [[None] * n for _ in range(m)]

    dp[0][0] = cost[0][0]

    # ---- fill first row (can only come from the left) ----
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + cost[0][j]
        prev[0][j] = (0, j - 1)

    # ---- fill first column (can only come from above) ----
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + cost[i][0]
        prev[i][0] = (i - 1, 0)

    # ---- fill the rest in deterministic row-major order ----
    for i in range(1, m):
        for j in range(1, n):
            up, left = dp[i - 1][j], dp[i][j - 1]
            if up <= left:                      # tie -> prefer UP (deterministic)
                dp[i][j] = cost[i][j] + up
                prev[i][j] = (i - 1, j)
            else:
                dp[i][j] = cost[i][j] + left
                prev[i][j] = (i, j - 1)

    # ---- reconstruct path from goal back to start ----
    path: List[Tuple[int, int]] = []
    cur: Union[None, Tuple[int, int]] = (m - 1, n - 1)
    while cur is not None:
        path.append(cur)
        cur = prev[cur[0]][cur[1]]
    path.reverse()

    return dp[m - 1][n - 1], path


if __name__ == "__main__":
    grid = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1],
    ]
    total, route = min_cost_path(grid)
    print("Minimum cost:", total)   # 7
    print("Path:", route)           # [(0, 0), (1, 0), (1, 1)?...] see below

    # Tie example: both routes cost 7; the tie rule prefers coming from above,
    # giving [(0,0), (0,1), (0,2), (1,2), (2,2)].
    assert total == 7
    assert route[0] == (0, 0) and route[-1] == (2, 2)
    assert min_cost_path([[5]]) == (5, [(0, 0)])
    assert min_cost_path([[1, 2, 3]]) == (6, [(0, 0), (0, 1), (0, 2)])
    assert min_cost_path([[1], [2], [3]]) == (6, [(0, 0), (1, 0), (2, 0)])
    # Determinism check
    assert min_cost_path(grid) == min_cost_path(grid)