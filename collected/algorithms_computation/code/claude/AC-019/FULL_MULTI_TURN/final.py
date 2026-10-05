"""
Minimum-Cost Grid Path (right/down moves only).

Input : rectangular, non-empty grid of finite, non-negative numbers.
Output: (minimum_cost, path)                    by default
        (minimum_cost, path, operation_summary) if include_summary=True
Method: dynamic programming with predecessor coordinates.
Tie   : if "up" and "left" cost the same, the predecessor is "up".
Invalid input (empty, ragged, non-numeric/bool, NaN, inf, negative,
or a path cost that overflows float range) raises ValueError.
Standard library only; fully deterministic.
"""
import math
from typing import Dict, List, Optional, Sequence, Tuple, Union

Number = float  # ints work too; arithmetic is type-preserving
Path = List[Tuple[int, int]]
Summary = Dict[str, int]


def min_cost_path(
    grid: Sequence[Sequence[Number]],
    include_summary: bool = False,
) -> Union[Tuple[Number, Path], Tuple[Number, Path, Summary]]:
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
            # Ints are always finite (and math.isfinite overflows on huge
            # ints), so only floats need the finiteness check.
            if isinstance(v, float) and not math.isfinite(v):
                raise ValueError("grid values must be finite")
            if v < 0:
                raise ValueError("grid values must be non-negative")

    # ---- DP tables --------------------------------------------------
    dp: List[List[Number]] = [[0] * cols for _ in range(rows)]
    prev: List[List[Optional[Tuple[int, int]]]] = [
        [None] * cols for _ in range(rows)
    ]
    dp[0][0] = grid[0][0]

    # Operation counters (bookkeeping only; never affect results).
    dp_cells_computed = 1
    forced_moves = 0
    interior_comparisons = 0
    chose_up = 0
    chose_left = 0
    tie_breaks = 0

    try:
        for c in range(1, cols):  # first row: only from the left
            dp[0][c] = dp[0][c - 1] + grid[0][c]
            prev[0][c] = (0, c - 1)
            dp_cells_computed += 1
            forced_moves += 1

        for r in range(1, rows):  # first column: only from above
            dp[r][0] = dp[r - 1][0] + grid[r][0]
            prev[r][0] = (r - 1, 0)
            dp_cells_computed += 1
            forced_moves += 1

        for r in range(1, rows):
            for c in range(1, cols):
                up, left = dp[r - 1][c], dp[r][c - 1]
                interior_comparisons += 1
                dp_cells_computed += 1
                if up <= left:  # tie -> prefer up (deterministic)
                    if up == left:
                        tie_breaks += 1
                    chose_up += 1
                    dp[r][c] = up + grid[r][c]
                    prev[r][c] = (r - 1, c)
                else:
                    chose_left += 1
                    dp[r][c] = left + grid[r][c]
                    prev[r][c] = (r, c - 1)
    except OverflowError:  # e.g. huge int + float
        raise ValueError("path cost is not representable")

    min_cost = dp[rows - 1][cols - 1]
    if isinstance(min_cost, float) and not math.isfinite(min_cost):
        raise ValueError("path cost overflows float range")

    # ---- Path reconstruction ---------------------------------------
    path: Path = []
    cur: Optional[Tuple[int, int]] = (rows - 1, cols - 1)
    while cur is not None:
        path.append(cur)
        cur = prev[cur[0]][cur[1]]
    path.reverse()

    if not include_summary:
        return min_cost, path  # original output, exactly

    summary: Summary = {
        "dp_cells_computed": dp_cells_computed,
        "forced_moves": forced_moves,
        "interior_comparisons": interior_comparisons,
        "chose_up": chose_up,
        "chose_left": chose_left,
        "tie_breaks": tie_breaks,
        "path_reconstruction_steps": len(path),
        "total_operations": dp_cells_computed + len(path),
    }
    return min_cost, path, summary


def _raises(grid) -> bool:
    for flag in (False, True):
        try:
            min_cost_path(grid, include_summary=flag)
        except ValueError:
            continue
        return False
    return True


if __name__ == "__main__":
    MAXF = 1.7976931348623157e308   # largest finite float
    TINY = 5e-324                   # smallest positive (denormal) float

    # ---- Original behavior preserved --------------------------------
    classic = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
    classic_path = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]
    assert min_cost_path(classic) == (7, classic_path)
    cost, path, s = min_cost_path(classic, include_summary=True)
    assert (cost, path) == (7, classic_path)
    assert s == {
        "dp_cells_computed": 9, "forced_moves": 4,
        "interior_comparisons": 4, "chose_up": 2, "chose_left": 2,
        "tie_breaks": 0, "path_reconstruction_steps": 5,
        "total_operations": 14,
    }
    cost, path, s = min_cost_path([[1, 1], [1, 1]], include_summary=True)
    assert (cost, path) == (3, [(0, 0), (0, 1), (1, 1)])
    assert s["tie_breaks"] == 1 and s["chose_up"] == 1

    # ---- Boundary: smallest / degenerate shapes ---------------------
    assert min_cost_path([[5]]) == (5, [(0, 0)])
    assert min_cost_path([[0]]) == (0, [(0, 0)])
    _, _, s = min_cost_path([[5]], include_summary=True)
    assert s["interior_comparisons"] == 0 and s["total_operations"] == 2
    assert min_cost_path([[1, 2, 3]]) == (6, [(0, 0), (0, 1), (0, 2)])
    assert min_cost_path([[1], [2], [3]]) == (6, [(0, 0), (1, 0), (2, 0)])

    # ---- Boundary: zero costs ---------------------------------------
    assert min_cost_path([[0, 0, 0], [0, 0, 0]]) == (
        0, [(0, 0), (0, 1), (0, 2), (1, 2)])          # ties -> up preferred
    c, p = min_cost_path([[0.0, -0.0], [-0.0, 0.0]])
    assert c == 0 and p == [(0, 0), (0, 1), (1, 1)]

    # ---- Boundary: smallest positive float --------------------------
    c, p = min_cost_path([[TINY, TINY], [TINY, TINY]])
    assert c == 3 * TINY and c > 0 and p == [(0, 0), (0, 1), (1, 1)]

    # ---- Boundary: largest finite float -----------------------------
    assert min_cost_path([[MAXF]]) == (MAXF, [(0, 0)])
    assert min_cost_path([[MAXF, 0.0], [0.0, 0.0]]) == (
        MAXF, [(0, 0), (0, 1), (1, 1)])                # tie -> up
    assert min_cost_path([[0.0, MAXF], [0.0, 0.0]]) == (
        0.0, [(0, 0), (1, 0), (1, 1)])                 # avoids the MAXF cell
    # An unchosen overflowing cell must not break a finite answer.
    c, p = min_cost_path([[0.0, MAXF, MAXF], [0.0, 0.0, 0.0]])
    assert c == 0.0 and p == [(0, 0), (1, 0), (1, 1), (1, 2)]

    # ---- Boundary: float overflow of the *result* raises ------------
    assert _raises([[MAXF, MAXF]])
    assert _raises([[MAXF], [MAXF]])
    assert _raises([[MAXF, MAXF], [MAXF, MAXF]])

    # ---- Boundary: huge ints (arbitrary precision, no overflow) -----
    BIG = 10 ** 400
    assert min_cost_path([[BIG, BIG]]) == (2 * BIG, [(0, 0), (0, 1)])
    assert min_cost_path([[BIG, 0], [0, 0]]) == (
        BIG, [(0, 0), (0, 1), (1, 1)])
    assert _raises([[BIG, 1.0]])                       # int + float overflow
    assert min_cost_path([[1, 2], [3, 4]])[0] == 7 and isinstance(
        min_cost_path([[1, 2], [3, 4]])[0], int)       # type-preserving

    # ---- Boundary: long thin grids (no recursion limits) ------------
    n = 2000
    c, p = min_cost_path([[1] * n])
    assert c == n and p == [(0, j) for j in range(n)]
    c, p = min_cost_path([[1] for _ in range(n)])
    assert c == n and p == [(i, 0) for i in range(n)]

    # ---- Boundary: uniform large grid, tie rule on every cell -------
    m = 60
    c, p = min_cost_path([[1] * m for _ in range(m)], include_summary=True)[:2]
    assert c == 2 * m - 1
    assert p == [(0, j) for j in range(m)] + [(i, m - 1) for i in range(1, m)]
    s = min_cost_path([[1] * m for _ in range(m)], include_summary=True)[2]
    assert s["tie_breaks"] == s["interior_comparisons"] == (m - 1) ** 2
    assert s["chose_up"] == (m - 1) ** 2 and s["chose_left"] == 0

    # ---- Invalid inputs still raise ValueError ----------------------
    for bad in [[], [[]], [[1, 2], [3]], [[-1]], [[-TINY]],
                [[float("nan")]], [[float("inf")]], [[-float("inf")]],
                [[True]], [["1"]], [[None]]]:
        assert _raises(bad), bad

    # ---- Determinism and invariants ---------------------------------
    g = [[2, 1, 4, 3], [5, 2, 1, 2], [1, 3, 2, 1]]
    a = min_cost_path(g, include_summary=True)
    assert a == min_cost_path(g, include_summary=True)
    s = a[2]
    assert s["chose_up"] + s["chose_left"] == s["interior_comparisons"]
    assert s["dp_cells_computed"] == 1 + s["forced_moves"] + s["interior_comparisons"]
    assert s["path_reconstruction_steps"] == len(a[1])

    print("all checks passed")