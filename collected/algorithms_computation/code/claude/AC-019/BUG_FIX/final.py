import math
from itertools import combinations, product
from numbers import Real
from typing import List, Optional, Tuple

Cell = Tuple[int, int]


def _validate(grid) -> Tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or len(grid) == 0:
        raise ValueError("grid must be a non-empty list of rows")
    if not isinstance(grid[0], (list, tuple)) or len(grid[0]) == 0:
        raise ValueError("grid rows must be non-empty lists")
    cols = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != cols:
            raise ValueError("grid must be rectangular")
        for v in row:
            if isinstance(v, bool) or not isinstance(v, Real):
                raise ValueError("costs must be real numbers")
            if math.isnan(v) or math.isinf(v):
                raise ValueError("costs must be finite")
            if v < 0:
                raise ValueError("costs must be non-negative")
    return len(grid), cols


def min_cost_path(grid: List[List[float]]) -> Tuple[float, List[Cell]]:
    """
    Return (minimum_cost, path), moving only right/down from the top-left
    to the bottom-right. Cost includes both endpoints.

    Tie rule: if the cost via the cell above equals the cost via the
    cell to the left, the predecessor is the cell ABOVE.
    """
    rows, cols = _validate(grid)

    dp: List[List[float]] = [[0] * cols for _ in range(rows)]
    pred: List[List[Optional[Cell]]] = [[None] * cols for _ in range(rows)]
    dp[0][0] = grid[0][0]

    for c in range(1, cols):                      # first row: only from left
        dp[0][c] = dp[0][c - 1] + grid[0][c]
        pred[0][c] = (0, c - 1)

    for r in range(1, rows):                      # first column: only from above
        dp[r][0] = dp[r - 1][0] + grid[r][0]
        pred[r][0] = (r - 1, 0)

    for r in range(1, rows):                      # interior cells
        for c in range(1, cols):
            from_up, from_left = dp[r - 1][c], dp[r][c - 1]
            if from_up <= from_left:              # tie -> up (deterministic)
                dp[r][c] = grid[r][c] + from_up
                pred[r][c] = (r - 1, c)
            else:
                dp[r][c] = grid[r][c] + from_left
                pred[r][c] = (r, c - 1)

    path: List[Cell] = []
    cur: Optional[Cell] = (rows - 1, cols - 1)
    while cur is not None:
        path.append(cur)
        cur = pred[cur[0]][cur[1]]
    path.reverse()
    return dp[rows - 1][cols - 1], path


def _brute_force_cost(grid) -> float:
    rows, cols = len(grid), len(grid[0])
    steps = rows + cols - 2
    best = None
    for downs in combinations(range(steps), rows - 1):
        ds = set(downs)
        r = c = 0
        total = grid[0][0]
        for i in range(steps):
            r, c = (r + 1, c) if i in ds else (r, c + 1)
            total += grid[r][c]
        best = total if best is None else min(best, total)
    return best


def main() -> None:
    print(min_cost_path([[1, 3, 1], [1, 5, 1], [4, 2, 1]]))
    print(min_cost_path([[1, 1], [1, 1]]))        # tie -> via (0, 1)
    print(min_cost_path([[7]]))
    print(min_cost_path([[1, 2, 3]]))
    print(min_cost_path([[1], [2], [3]]))

    for bad in ([[1, float("nan")], [2, 3]], [[1, "a"]], [[True, 2]], [[1], [2, 3]]):
        try:
            min_cost_path(bad)
        except ValueError as e:
            print("rejected:", e)

    # Cross-check against brute force for every 2x3 grid with values 0..2.
    for vals in product(range(3), repeat=6):
        grid = [list(vals[:3]), list(vals[3:])]
        cost, path = min_cost_path(grid)
        assert cost == _brute_force_cost(grid)
        assert sum(grid[r][c] for r, c in path) == cost
        assert path[0] == (0, 0) and path[-1] == (1, 2)
        assert all((b[0] - a[0], b[1] - a[1]) in ((1, 0), (0, 1))
                   for a, b in zip(path, path[1:]))
    print("all checks passed")


if __name__ == "__main__":
    main()