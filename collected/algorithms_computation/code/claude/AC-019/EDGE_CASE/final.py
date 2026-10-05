"""
MINIMUM-COST GRID PATH  (restated)
==================================
Given a non-empty rectangular m x n matrix `cost` of non-negative numbers,
start at the top-left cell (0, 0) and reach the bottom-right cell (m-1, n-1)
moving only RIGHT (r, c+1) or DOWN (r+1, c). A path's cost is the sum of the
costs of every cell it visits, including both endpoints.

Required output: (min_cost, path)
    min_cost : the minimum total cost
    path     : list of (row, col) tuples from (0, 0) to (m-1, n-1), ONE
               optimal path, chosen deterministically.

Rules preserved from the original solution
------------------------------------------
- DP: dp[i][j] = cost[i][j] + min(dp[i-1][j], dp[i][j-1]) (existing neighbours only).
- prev[i][j] stores the predecessor coordinates.
- TIE RULE: if dp[i-1][j] == dp[i][j-1], the predecessor is ABOVE (i-1, j).
- Cells are filled in fixed row-major order; the path is rebuilt by walking
  prev[][] back from the goal and reversing.
- Standard library only; no network, randomness, or user interaction.

Boundary / difficult cases now handled explicitly
-------------------------------------------------
- 1x1 grid (start == goal, path has a single cell, cost counted once).
- Single row (1xN) and single column (Mx1): only one possible path.
- All-zero grids (every cell is a tie, so the tie rule decides the whole path).
- Zero-cost cells mixed with large values.
- Very large integers (Python ints are arbitrary precision, so no overflow;
  sums beyond 2**63 - 1 stay exact).
- Floats, including 0.0 and -0.0; NaN and +/-inf are rejected because
  NaN would silently defeat the non-negativity check and comparisons.
- Very long / large grids: everything is iterative (no recursion), so there
  is no recursion-limit risk.
- Invalid input (empty, ragged, negative, NaN/inf) raises ValueError.
- The input matrix is never mutated.
"""

import math
import unittest
from itertools import product
from typing import List, Sequence, Tuple, Union

Number = Union[int, float]
Cell = Tuple[int, int]


def _validate(cost: Sequence[Sequence[Number]]) -> Tuple[int, int]:
    if not cost or not cost[0]:
        raise ValueError("cost matrix must be non-empty")
    m, n = len(cost), len(cost[0])
    for row in cost:
        if len(row) != n:
            raise ValueError("cost matrix must be rectangular")
        for v in row:
            if isinstance(v, float) and not math.isfinite(v):
                raise ValueError("costs must be finite (no NaN/inf)")
            if v < 0:
                raise ValueError("costs must be non-negative")
    return m, n


def min_cost_path(cost: Sequence[Sequence[Number]]) -> Tuple[Number, List[Cell]]:
    m, n = _validate(cost)

    dp: List[List[Number]] = [[0] * n for _ in range(m)]
    prev: List[List[Union[None, Cell]]] = [[None] * n for _ in range(m)]

    # Start cell (also the goal when m == n == 1; counted exactly once).
    dp[0][0] = cost[0][0]

    # First row: only reachable from the left.
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + cost[0][j]
        prev[0][j] = (0, j - 1)

    # First column: only reachable from above.
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + cost[i][0]
        prev[i][0] = (i - 1, 0)

    # Interior cells in fixed row-major order.
    for i in range(1, m):
        for j in range(1, n):
            up, left = dp[i - 1][j], dp[i][j - 1]
            if up <= left:                       # tie -> prefer UP (unchanged rule)
                dp[i][j] = cost[i][j] + up
                prev[i][j] = (i - 1, j)
            else:
                dp[i][j] = cost[i][j] + left
                prev[i][j] = (i, j - 1)

    # Reconstruct path (iterative) from goal back to start.
    path: List[Cell] = []
    cur: Union[None, Cell] = (m - 1, n - 1)
    while cur is not None:
        path.append(cur)
        cur = prev[cur[0]][cur[1]]
    path.reverse()

    return dp[m - 1][n - 1], path


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

def _check_path(tc: unittest.TestCase, cost, total, path):
    """Path starts/ends correctly, uses only right/down steps, and sums to total."""
    m, n = len(cost), len(cost[0])
    tc.assertEqual(path[0], (0, 0))
    tc.assertEqual(path[-1], (m - 1, n - 1))
    tc.assertEqual(len(path), m + n - 1)
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        tc.assertIn((r2 - r1, c2 - c1), ((0, 1), (1, 0)))
    tc.assertEqual(sum(cost[r][c] for r, c in path), total)


def _brute_force_min(cost) -> Number:
    m, n = len(cost), len(cost[0])

    def go(i, j):
        if i == m - 1 and j == n - 1:
            return cost[i][j]
        best = None
        if i + 1 < m:
            best = go(i + 1, j)
        if j + 1 < n:
            r = go(i, j + 1)
            best = r if best is None or r < best else best
        return cost[i][j] + best

    return go(0, 0)


class TestMinCostPath(unittest.TestCase):
    # ---- original behaviour preserved ----
    def test_original_sample(self):
        grid = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
        total, path = min_cost_path(grid)
        self.assertEqual(total, 7)
        self.assertEqual(path, [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)])
        _check_path(self, grid, total, path)

    def test_tie_prefers_up(self):
        # At (1,1): up = 5, left = 5 -> tie -> predecessor must be ABOVE (0,1).
        grid = [[0, 5], [5, 0]]
        self.assertEqual(min_cost_path(grid), (5, [(0, 0), (0, 1), (1, 1)]))

    # ---- 1x1 ----
    def test_single_cell_zero(self):
        self.assertEqual(min_cost_path([[0]]), (0, [(0, 0)]))

    def test_single_cell_nonzero(self):
        self.assertEqual(min_cost_path([[5]]), (5, [(0, 0)]))

    def test_single_cell_huge(self):
        big = 10 ** 30
        self.assertEqual(min_cost_path([[big]]), (big, [(0, 0)]))

    # ---- single row / single column ----
    def test_single_row(self):
        self.assertEqual(min_cost_path([[1, 2, 3]]), (6, [(0, 0), (0, 1), (0, 2)]))

    def test_single_column(self):
        self.assertEqual(min_cost_path([[1], [2], [3]]), (6, [(0, 0), (1, 0), (2, 0)]))

    def test_very_long_single_row(self):
        n = 100_000
        total, path = min_cost_path([[1] * n])
        self.assertEqual(total, n)
        self.assertEqual(path, [(0, j) for j in range(n)])

    def test_very_long_single_column(self):
        m = 100_000
        total, path = min_cost_path([[1] for _ in range(m)])
        self.assertEqual(total, m)
        self.assertEqual(path, [(i, 0) for i in range(m)])

    # ---- all zeros: every cell is a tie ----
    def test_all_zero_3x3_tie_path(self):
        grid = [[0] * 3 for _ in range(3)]
        self.assertEqual(
            min_cost_path(grid),
            (0, [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]),
        )

    def test_all_zero_large_grid(self):
        m = n = 300
        grid = [[0] * n for _ in range(m)]
        total, path = min_cost_path(grid)
        self.assertEqual(total, 0)
        # Tie -> up everywhere: go right along row 0, then down the last column.
        expected = [(0, j) for j in range(n)] + [(i, n - 1) for i in range(1, m)]
        self.assertEqual(path, expected)

    # ---- large magnitudes ----
    def test_values_beyond_int64(self):
        big = 2 ** 63 - 1
        grid = [[big, big], [big, big]]
        total, path = min_cost_path(grid)
        self.assertEqual(total, 3 * big)          # exceeds int64, still exact
        self.assertEqual(path, [(0, 0), (0, 1), (1, 1)])

    def test_zero_cells_next_to_huge_cells(self):
        big = 10 ** 18
        grid = [[0, big, big], [0, 0, big], [big, 0, 0]]
        total, path = min_cost_path(grid)
        self.assertEqual(total, 0)
        self.assertEqual(path, [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)])
        _check_path(self, grid, total, path)

    # ---- floats ----
    def test_float_and_negative_zero(self):
        grid = [[0.0, 0.5], [-0.0, 0.25]]
        total, path = min_cost_path(grid)
        self.assertEqual(total, 0.25)
        self.assertEqual(path, [(0, 0), (1, 0), (1, 1)])

    # ---- non-mutation / determinism ----
    def test_input_not_mutated_and_deterministic(self):
        grid = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
        snapshot = [row[:] for row in grid]
        first = min_cost_path(grid)
        second = min_cost_path(grid)
        self.assertEqual(first, second)
        self.assertEqual(grid, snapshot)

    # ---- exhaustive small-grid cross-check against brute force ----
    def test_bruteforce_agreement_small_grids(self):
        for m, n in [(1, 1), (1, 3), (3, 1), (2, 2), (2, 3), (3, 2), (3, 3)]:
            for vals in product((0, 1, 2), repeat=m * n if m * n <= 6 else 0):
                grid = [list(vals[r * n:(r + 1) * n]) for r in range(m)]
                total, path = min_cost_path(grid)
                self.assertEqual(total, _brute_force_min(grid))
                _check_path(self, grid, total, path)
        # 3x3 with values {0, 1}: 512 grids, still instant.
        for vals in product((0, 1), repeat=9):
            grid = [list(vals[r * 3:(r + 1) * 3]) for r in range(3)]
            total, path = min_cost_path(grid)
            self.assertEqual(total, _brute_force_min(grid))
            _check_path(self, grid, total, path)

    # ---- invalid input ----
    def test_invalid_inputs(self):
        for bad in (
            [],
            [[]],
            [[1, 2], [3]],                 # ragged
            [[1, -1]],                     # negative
            [[-0.0001]],                   # tiny negative float
            [[float("nan")]],              # NaN
            [[1.0, float("inf")]],         # infinity
        ):
            with self.assertRaises(ValueError, msg=repr(bad)):
                min_cost_path(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)