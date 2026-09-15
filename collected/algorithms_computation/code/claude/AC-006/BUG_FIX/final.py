"""
PROBLEM
-------
Given a numeric grid and a threshold T, find the largest 4-connected
(up/down/left/right, no diagonals) region of cells whose value is >= T.

Return, for the winning region:
    - size:       number of cells in the region
    - perimeter:  number of exposed sides (a side is exposed if the
                  neighbor across it is out of bounds OR has value < T)
    - coordinate: the smallest (row, col) among the region's cells
                  (lexicographic order: smallest row first, then col)

Tie-breaking when multiple regions share the maximum size:
    1. larger perimeter wins
    2. if still tied, smaller coordinate wins

KEY CONSTRAINTS
---------------
- Grid must be a non-empty, rectangular 2D sequence of numbers.
- Must use ITERATIVE flood fill (explicit stack) -- no recursion.
- Deterministic: same input always yields the same output, resolved by
  a single unambiguous comparison key -- no sentinel/guard duality.
- Standard library only. No network/API calls, no randomness, no
  external services, no human interaction.

REQUIRED OUTPUT
----------------
RegionResult(size, perimeter, coordinate) for the largest region,
or RegionResult(0, 0, None) if no cell meets the threshold.

ALGORITHM
---------
1. A cell "qualifies" if grid[r][c] >= T.
2. Scan cells in row-major order. For each unvisited qualifying cell,
   run an iterative (stack-based) flood fill to gather its whole
   4-connected component.
3. While filling, for every popped cell, check its 4 neighbors:
     - in-bounds & qualifying & unvisited -> mark visited, push it
     - in-bounds & qualifying & visited   -> interior link, not exposed
     - out of bounds OR value < T        -> exposed side, perimeter += 1
4. size = cell count, coordinate = min(cells).
5. Collect (size, perimeter, coordinate) for EVERY region into a list,
   then select the best with one explicit sort key:
       key = (-size, -perimeter, coordinate)
   and take the minimum -- this is the single source of truth for tie
   handling; there is no separate "first candidate" special case.
"""

from typing import List, Optional, NamedTuple, Sequence, Tuple


class RegionResult(NamedTuple):
    size: int
    perimeter: int
    coordinate: Optional[tuple]  # (row, col) or None if no region exists


def _validate_grid(grid: Sequence[Sequence[float]]) -> None:
    if not isinstance(grid, (list, tuple)) or len(grid) == 0:
        raise ValueError("grid must be a non-empty 2D sequence")
    row_len = len(grid[0])
    if row_len == 0:
        raise ValueError("grid rows must be non-empty")
    for r, row in enumerate(grid):
        if len(row) != row_len:
            raise ValueError(f"grid is ragged: row {r} has length "
                              f"{len(row)}, expected {row_len}")


def _flood_fill(grid, visited, n_rows, n_cols, threshold, start_r, start_c
                 ) -> Tuple[int, int, tuple]:
    """Iterative 4-connected flood fill. Returns (size, perimeter, min_coord)."""

    def qualifies(r: int, c: int) -> bool:
        return grid[r][c] >= threshold

    visited[start_r][start_c] = True
    stack = [(start_r, start_c)]
    region_cells = []
    perimeter = 0

    while stack:
        r, c = stack.pop()
        region_cells.append((r, c))

        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n_rows and 0 <= nc < n_cols:
                if qualifies(nr, nc):
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
                    # already-visited qualifying neighbor -> interior
                    # link, correctly NOT counted as exposed
                else:
                    perimeter += 1  # neighbor fails threshold
            else:
                perimeter += 1  # neighbor is out of grid bounds

    size = len(region_cells)
    coord = min(region_cells)
    return size, perimeter, coord


def largest_threshold_region(grid: Sequence[Sequence[float]],
                              threshold: float) -> RegionResult:
    """
    Find the largest 4-connected region of cells with value >= threshold.

    Deterministic tie handling: among all discovered regions, exactly one
    explicit key (-size, -perimeter, coordinate) is minimized -- larger
    size wins, then larger perimeter, then smaller coordinate. There is
    no separate first-candidate special case; every region (including
    the first) is compared the same way.
    """
    _validate_grid(grid)

    n_rows = len(grid)
    n_cols = len(grid[0])
    visited = [[False] * n_cols for _ in range(n_rows)]

    regions: List[Tuple[int, int, tuple]] = []

    for start_r in range(n_rows):
        for start_c in range(n_cols):
            if visited[start_r][start_c]:
                continue
            if grid[start_r][start_c] < threshold:
                continue
            regions.append(
                _flood_fill(grid, visited, n_rows, n_cols, threshold,
                             start_r, start_c)
            )

    if not regions:
        return RegionResult(0, 0, None)

    best_size, best_perimeter, best_coord = min(
        regions, key=lambda reg: (-reg[0], -reg[1], reg[2])
    )
    return RegionResult(best_size, best_perimeter, best_coord)


def _demo() -> None:
    grid = [
        [5, 5, 1, 9],
        [5, 5, 1, 9],
        [1, 1, 1, 9],
        [8, 8, 1, 9],
    ]
    T = 5
    result = largest_threshold_region(grid, T)
    print("Grid:")
    for row in grid:
        print(row)
    print(f"Threshold: {T}")
    print(f"Result -> size={result.size}, perimeter={result.perimeter}, "
          f"coordinate={result.coordinate}")

    grid2 = [
        [9, 0, 9],
        [9, 0, 9],
    ]
    T2 = 5
    result2 = largest_threshold_region(grid2, T2)
    print("\nGrid 2 (equal size AND perimeter tie):")
    for row in grid2:
        print(row)
    print(f"Threshold: {T2}")
    print(f"Result -> size={result2.size}, perimeter={result2.perimeter}, "
          f"coordinate={result2.coordinate}  (expect coordinate=(0, 0))")

    grid3 = [[1, 2], [3, 4]]
    result3 = largest_threshold_region(grid3, 100)
    print("\nGrid 3 (no qualifying cells):")
    print(f"Result -> {result3}")


if __name__ == "__main__":
    _demo()