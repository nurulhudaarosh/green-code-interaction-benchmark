from typing import List, Optional, Tuple

Cell = Tuple[int, int]


def min_cost_path(grid: List[List[float]]) -> Tuple[float, List[Cell]]:
    """
    Return (minimum_cost, path) for moving only right/down from the
    top-left to the bottom-right of a non-negative cost grid.

    Tie rule: if arriving from above and from the left cost the same,
    the predecessor is the cell ABOVE. This makes the path deterministic.
    """
    # ---- validation ----
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    rows, cols = len(grid), len(grid[0])
    for row in grid:
        if len(row) != cols:
            raise ValueError("grid must be rectangular")
        for v in row:
            if v < 0:
                raise ValueError("costs must be non-negative")

    # ---- DP tables ----
    dp: List[List[float]] = [[0] * cols for _ in range(rows)]
    pred: List[List[Optional[Cell]]] = [[None] * cols for _ in range(rows)]

    dp[0][0] = grid[0][0]

    # First row: can only come from the left.
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + grid[0][c]
        pred[0][c] = (0, c - 1)

    # First column: can only come from above.
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + grid[r][0]
        pred[r][0] = (r - 1, 0)

    # Interior cells.
    for r in range(1, rows):
        for c in range(1, cols):
            from_up = dp[r - 1][c]
            from_left = dp[r][c - 1]
            if from_up <= from_left:          # tie -> up (deterministic)
                dp[r][c] = grid[r][c] + from_up
                pred[r][c] = (r - 1, c)
            else:
                dp[r][c] = grid[r][c] + from_left
                pred[r][c] = (r, c - 1)

    # ---- backtrack ----
    path: List[Cell] = []
    cur: Optional[Cell] = (rows - 1, cols - 1)
    while cur is not None:
        path.append(cur)
        cur = pred[cur[0]][cur[1]]
    path.reverse()

    return dp[rows - 1][cols - 1], path


def main() -> None:
    grid = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1],
    ]
    cost, path = min_cost_path(grid)
    print("Minimum cost:", cost)
    print("Path:", path)

    # Tie example: multiple optimal paths exist; "up" is preferred.
    tie_grid = [
        [1, 1],
        [1, 1],
    ]
    print(min_cost_path(tie_grid))

    # Edge cases
    print(min_cost_path([[7]]))            # single cell
    print(min_cost_path([[1, 2, 3]]))      # single row
    print(min_cost_path([[1], [2], [3]]))  # single column


if __name__ == "__main__":
    main()