from typing import Dict, List, Optional, Tuple, Union

Coord = Tuple[int, int]
Summary = Dict[str, int]


def min_cost_path(
    grid: List[List[float]],
    include_operation_summary: bool = False,
) -> Union[Tuple[float, List[Coord]], Tuple[float, List[Coord], Summary]]:
    """
    Minimum-cost path moving only right/down from (0, 0) to (m-1, n-1).

    Default (include_operation_summary=False): returns (min_cost, path),
    identical to the original behavior.

    If include_operation_summary=True: returns (min_cost, path, summary).

    Tie rule: equal cost from above and from the left -> predecessor is above.
    """
    # ---- Validation (unchanged) ----
    if not grid or not grid[0]:
        raise ValueError("grid must be a non-empty matrix")
    m, n = len(grid), len(grid[0])
    for row in grid:
        if len(row) != n:
            raise ValueError("grid must be rectangular")
        for v in row:
            if v < 0:
                raise ValueError("costs must be non-negative")

    # ---- Counters (observe only; never affect results) ----
    cells_initialized = 0
    forced_moves = 0
    comparisons = 0
    chose_up = 0
    chose_left = 0
    ties_broken_up = 0

    # ---- DP tables ----
    dp: List[List[float]] = [[0] * n for _ in range(m)]
    prev: List[List[Optional[Coord]]] = [[None] * n for _ in range(m)]

    dp[0][0] = grid[0][0]
    cells_initialized += 1

    for c in range(1, n):                      # first row: from the left
        dp[0][c] = dp[0][c - 1] + grid[0][c]
        prev[0][c] = (0, c - 1)
        forced_moves += 1

    for r in range(1, m):                      # first column: from above
        dp[r][0] = dp[r - 1][0] + grid[r][0]
        prev[r][0] = (r - 1, 0)
        forced_moves += 1

    for r in range(1, m):                      # interior cells
        for c in range(1, n):
            from_up = dp[r - 1][c]
            from_left = dp[r][c - 1]
            comparisons += 1
            if from_up <= from_left:           # tie -> prefer "up"
                dp[r][c] = grid[r][c] + from_up
                prev[r][c] = (r - 1, c)
                chose_up += 1
                if from_up == from_left:
                    ties_broken_up += 1
            else:
                dp[r][c] = grid[r][c] + from_left
                prev[r][c] = (r, c - 1)
                chose_left += 1

    # ---- Path reconstruction ----
    path: List[Coord] = []
    cur: Optional[Coord] = (m - 1, n - 1)
    while cur is not None:
        path.append(cur)
        cur = prev[cur[0]][cur[1]]
    path.reverse()

    min_cost = dp[m - 1][n - 1]

    if not include_operation_summary:
        return min_cost, path                  # original output, unchanged

    backtrack_steps = len(path) - 1
    summary: Summary = {
        "rows": m,
        "cols": n,
        "cells_initialized": cells_initialized,
        "forced_moves": forced_moves,
        "comparisons": comparisons,
        "chose_up": chose_up,
        "chose_left": chose_left,
        "ties_broken_up": ties_broken_up,
        "backtrack_steps": backtrack_steps,
        "total_operations": (
            cells_initialized + forced_moves + comparisons + backtrack_steps
        ),
    }
    return min_cost, path, summary


def main() -> None:
    g = [[1, 3, 1],
         [1, 5, 1],
         [4, 2, 1]]

    # Feature disabled: original behavior.
    print("disabled:", min_cost_path(g))

    # Feature enabled.
    cost, path, summary = min_cost_path(g, include_operation_summary=True)
    print("enabled: ")
    print("  min_cost         =", cost)
    print("  path             =", path)
    print("  operation_summary =", summary)

    # Tie example.
    t = [[1, 1], [1, 1]]
    print("tie:", min_cost_path(t, include_operation_summary=True))


if __name__ == "__main__":
    main()