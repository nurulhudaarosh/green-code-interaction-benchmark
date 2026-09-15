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
- Must use ITERATIVE flood fill (explicit stack) -- no recursion --
  so large grids don't hit Python's recursion limit.
- Deterministic: same input always yields the same output. Traversal
  order never changes a region's own size/perimeter/coordinate; the
  tie-break rule fully resolves ambiguity when sizes match.
- Standard library only. No network/API calls, no randomness, no
  external services, no human interaction.

REQUIRED OUTPUT
----------------
A RegionResult(size, perimeter, coordinate) for the largest region,
or RegionResult(0, 0, None) if no cell meets the threshold.

ALGORITHM
---------
1. A cell "qualifies" if grid[r][c] >= T.
2. Scan cells in row-major order. For each unvisited qualifying cell,
   run an iterative (stack-based) flood fill to gather its whole
   4-connected component.
3. While filling, for every cell popped, check its 4 neighbors:
     - in-bounds & qualifying & unvisited -> mark visited, push it
     - in-bounds & qualifying & visited   -> interior link, not exposed
     - out of bounds OR value < T        -> exposed side, perimeter += 1
4. After the fill: size = cell count, coordinate = min(cells).
5. Compare region to best-so-far via key (-size, -perimeter, coordinate)
   and keep the smallest key (implements: larger size wins, then larger
   perimeter, then smaller coordinate).
"""

from typing import List, Optional, NamedTuple, Sequence


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


def largest_threshold_region(grid: Sequence[Sequence[float]],
                              threshold: float) -> RegionResult:
    """
    Find the largest 4-connected region of cells with value >= threshold.

    Args:
        grid: rectangular 2D sequence of numbers.
        threshold: minimum value (inclusive) for a cell to qualify.

    Returns:
        RegionResult(size, perimeter, coordinate). If no cell qualifies,
        returns RegionResult(0, 0, None).
    """
    _validate_grid(grid)

    n_rows = len(grid)
    n_cols = len(grid[0])

    def qualifies(r: int, c: int) -> bool:
        return grid[r][c] >= threshold

    visited = [[False] * n_cols for _ in range(n_rows)]

    best_size = -1
    best_perimeter = -1
    best_coord = None

    # Deterministic scan order: row-major.
    for start_r in range(n_rows):
        for start_c in range(n_cols):
            if visited[start_r][start_c]:
                continue
            if not qualifies(start_r, start_c):
                continue

            # --- iterative flood fill (explicit stack, no recursion) ---
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
                            # already-visited qualifying neighbor ->
                            # interior link, not exposed, no count
                        else:
                            perimeter += 1  # neighbor fails threshold
                    else:
                        perimeter += 1  # neighbor is out of grid bounds
            # --- end flood fill ---

            size = len(region_cells)
            coord = min(region_cells)  # smallest (row, col)

            candidate_key = (-size, -perimeter, coord)
            best_key = (-best_size, -best_perimeter,
                        best_coord if best_coord is not None else (n_rows, n_cols))

            if best_coord is None or candidate_key < best_key:
                best_size = size
                best_perimeter = perimeter
                best_coord = coord

    if best_coord is None:
        return RegionResult(0, 0, None)

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
        [9, 9, 0, 9],
        [0, 0, 0, 9],
        [9, 9, 0, 9],
        [9, 9, 0, 0],
    ]
    T2 = 5
    result2 = largest_threshold_region(grid2, T2)
    print("\nGrid 2:")
    for row in grid2:
        print(row)
    print(f"Threshold: {T2}")
    print(f"Result -> size={result2.size}, perimeter={result2.perimeter}, "
          f"coordinate={result2.coordinate}")

    grid3 = [[1, 2], [3, 4]]
    result3 = largest_threshold_region(grid3, 100)
    print("\nGrid 3 (no qualifying cells):")
    print(f"Result -> {result3}")


if __name__ == "__main__":
    _demo()