"""
================================================================================
PROBLEM
================================================================================
Given a numeric 2D grid and a threshold T, find the largest 4-connected
region of cells whose value is >= T ("active" cells). Two active cells are
in the same region if connected through a chain of active cells using only
up/down/left/right steps (no diagonals).

For the largest region, return:
    - size       : number of cells in the region
    - perimeter  : number of exposed sides. A side of a cell counts as
                   exposed if it faces outside the grid boundary, or faces
                   a neighboring cell with value < T. (A neighbor with
                   value >= T can never be "exposed" against, since by
                   4-connectivity it would already be part of the same
                   region.)
    - coord      : the smallest (row, col) coordinate contained in the
                   region, under normal tuple ordering (row first, then
                   column).

Tie-breaking, in order, when multiple regions share the same size:
    1. Larger size wins outright (not a tie).
    2. If sizes are equal, the region with the larger perimeter wins.
    3. If perimeter also ties, the region with the smaller (row, col)
       coordinate wins.

================================================================================
KEY CONSTRAINTS
================================================================================
- The grid is rectangular: every row has the same length. An empty grid,
  or a grid with empty rows, is valid input and simply yields no region.
- Connectivity is strictly 4-directional (no diagonal merging).
- The algorithm must be deterministic: identical input always yields
  identical output, including consistent scan order (row-major) and
  consistent tie-break resolution.
- Flood fill must be iterative (explicit stack), not recursive, to avoid
  recursion-depth failures on large grids.
- Overall time complexity should be O(rows * cols): each cell is visited
  and finalized exactly once.
- No network access, external APIs/services, randomness, or human
  interaction; standard library only.

================================================================================
REQUIRED OUTPUT
================================================================================
For the best region found: (size, perimeter, smallest_coord).
If no cell meets the threshold (or the grid is empty), the result is None.

================================================================================
ALGORITHM
================================================================================
1. Scan the grid in row-major order.
2. On finding an unvisited active cell (value >= T), start a new region
   via an ITERATIVE flood fill using an explicit stack:
     - Mark cells visited as soon as they are pushed, to avoid duplicate
       queuing.
     - For each popped cell, increment size, update the running minimum
       coordinate, and examine all 4 neighbor directions:
         * out of bounds            -> perimeter += 1 (exposed side)
         * in bounds, value < T     -> perimeter += 1 (exposed side)
         * in bounds, value >= T,
           not yet visited          -> mark visited, push (part of region)
         * in bounds, value >= T,
           already visited          -> already counted/queued, skip
3. After the fill completes, compare (size, perimeter, min_coord) against
   the current best result using the tie-break rule above, and keep the
   winner.
4. After scanning the entire grid, the best region found is the answer.

Each cell is pushed/popped exactly once and does O(1) neighbor work, so
the whole algorithm runs in O(rows * cols) time and space.
================================================================================
"""

from typing import List, Optional, Sequence, Tuple, NamedTuple


class RegionResult(NamedTuple):
    size: int
    perimeter: int
    coord: Tuple[int, int]  # smallest (row, col) in the region


def largest_region(grid: Sequence[Sequence[float]], T: float) -> Optional[RegionResult]:
    """
    Find the largest 4-connected region of cells with value >= T.

    Args:
        grid: rectangular 2D sequence of numbers (all rows same length).
        T: threshold; a cell is "active" if grid[r][c] >= T.

    Returns:
        RegionResult(size, perimeter, coord) for the best region,
        or None if the grid is empty or no cell meets the threshold.

    Raises:
        ValueError: if the grid rows are not all the same length.
    """
    if not grid or not grid[0]:
        return None

    rows = len(grid)
    cols = len(grid[0])
    for r, row in enumerate(grid):
        if len(row) != cols:
            raise ValueError(f"Row {r} has length {len(row)}, expected {cols}")

    visited = [[False] * cols for _ in range(rows)]
    best: Optional[RegionResult] = None

    DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for i in range(rows):
        for j in range(cols):
            if visited[i][j] or grid[i][j] < T:
                continue

            # New region found at (i, j) -- iterative flood fill.
            visited[i][j] = True
            stack = [(i, j)]
            size = 0
            perimeter = 0
            min_coord = (i, j)

            while stack:
                r, c = stack.pop()
                size += 1
                if (r, c) < min_coord:
                    min_coord = (r, c)

                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if grid[nr][nc] >= T:
                            if not visited[nr][nc]:
                                visited[nr][nc] = True
                                stack.append((nr, nc))
                            # else: already visited/queued, nothing to add
                        else:
                            perimeter += 1  # blocked by low-value neighbor
                    else:
                        perimeter += 1  # blocked by grid boundary

            candidate = RegionResult(size, perimeter, min_coord)

            if best is None:
                best = candidate
            elif candidate.size > best.size:
                best = candidate
            elif candidate.size == best.size:
                if candidate.perimeter > best.perimeter:
                    best = candidate
                elif candidate.perimeter == best.perimeter:
                    if candidate.coord < best.coord:
                        best = candidate

    return best


def _format_result(result: Optional[RegionResult]) -> str:
    if result is None:
        return "No region found (empty grid or no cell meets threshold)."
    return (
        f"size={result.size}, "
        f"perimeter={result.perimeter}, "
        f"smallest_coord={result.coord}"
    )


def _self_test() -> None:
    """A few fixed, hand-checkable cases (no randomness)."""

    # Case 1: a small top-left blob vs. a right-column region that
    # merges (via vertical adjacency at column 3) with the bottom-right
    # corner into one larger region.
    grid1 = [
        [5, 5, 0, 3],
        [5, 0, 0, 3],
        [0, 0, 0, 3],
        [1, 1, 9, 9],
    ]
    # Region A: (0,0),(0,1),(1,0) -> size 3
    # Region B: (0,3),(1,3),(2,3),(3,3),(3,2) -> size 5 (column of 3's
    #   connects down into the 9,9 corner at row 3)
    result1 = largest_region(grid1, 3)
    assert result1.size == 5
    assert result1.coord == (0, 3)
    print("Case 1:", _format_result(result1))

    # Case 2: entire grid is one region.
    grid2 = [
        [1, 1],
        [1, 1],
    ]
    result2 = largest_region(grid2, 1)
    assert result2.size == 4
    assert result2.perimeter == 8  # full boundary of a 2x2 block
    assert result2.coord == (0, 0)
    print("Case 2:", _format_result(result2))

    # Case 3: no cell meets threshold.
    grid3 = [
        [1, 2],
        [3, 4],
    ]
    result3 = largest_region(grid3, 10)
    assert result3 is None
    print("Case 3:", _format_result(result3))

    # Case 4: empty grid.
    result4 = largest_region([], 1)
    assert result4 is None
    print("Case 4:", _format_result(result4))

    # Case 5: single cell above threshold.
    grid5 = [[7]]
    result5 = largest_region(grid5, 7)
    assert result5 == RegionResult(1, 4, (0, 0))
    print("Case 5:", _format_result(result5))

    print("All self-tests passed.")


if __name__ == "__main__":
    _self_test()