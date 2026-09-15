"""
Largest 4-connected region (value >= T) finder.
Deterministic, standard-library-only. Iterative flood fill; counts every exposed side.
"""

from typing import List, NamedTuple, Optional, Tuple


class RegionResult(NamedTuple):
    size: int
    perimeter: int
    coordinate: Optional[Tuple[int, int]]
    cells: Tuple[Tuple[int, int], ...]


def _validate_grid(grid: List[List[float]]) -> Tuple[int, int]:
    if not grid or not grid[0]:
        return 0, 0
    width = len(grid[0])
    for r, row in enumerate(grid):
        if len(row) != width:
            raise ValueError(f"Ragged grid: row {r} has length {len(row)}, expected {width}")
    return len(grid), width


def _flood_fill(
    grid: List[List[float]],
    visited: List[List[bool]],
    start: Tuple[int, int],
    threshold: float,
    rows: int,
    cols: int,
) -> Tuple[int, int, Tuple[int, int], List[Tuple[int, int]]]:
    stack = [start]
    visited[start[0]][start[1]] = True

    size = 0
    perimeter = 0
    smallest = start
    cells: List[Tuple[int, int]] = []
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while stack:
        r, c = stack.pop()
        size += 1
        cells.append((r, c))
        if (r, c) < smallest:
            smallest = (r, c)

        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                perimeter += 1
                continue
            if grid[nr][nc] < threshold:
                perimeter += 1
                continue
            if not visited[nr][nc]:
                visited[nr][nc] = True
                stack.append((nr, nc))

    return size, perimeter, smallest, cells


def _region_key(size: int, perimeter: int, coord: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """
    Explicit sort key enforcing the exact tie-break rule:
      1) larger size wins      -> negate for ascending comparison
      2) larger perimeter wins -> negate for ascending comparison
      3) smaller coordinate wins -> use as-is
    Comparing keys with '<' (min) now directly implements the full rule,
    removing all ad-hoc boolean chaining.
    """
    return (-size, -perimeter, coord[0], coord[1])


def largest_region(grid: List[List[float]], threshold: float) -> RegionResult:
    rows, cols = _validate_grid(grid)
    if rows == 0 or cols == 0:
        return RegionResult(size=0, perimeter=0, coordinate=None, cells=())

    visited = [[False] * cols for _ in range(rows)]

    best_key: Optional[Tuple[int, int, int, int]] = None
    best_size = 0
    best_perimeter = 0
    best_coord: Optional[Tuple[int, int]] = None
    best_cells: Tuple[Tuple[int, int], ...] = ()

    for r in range(rows):
        for c in range(cols):
            if visited[r][c] or grid[r][c] < threshold:
                continue

            size, perimeter, coord, cells = _flood_fill(
                grid, visited, (r, c), threshold, rows, cols
            )
            key = _region_key(size, perimeter, coord)

            if best_key is None or key < best_key:
                best_key = key
                best_size = size
                best_perimeter = perimeter
                best_coord = coord
                best_cells = tuple(cells)

    if best_coord is None:
        return RegionResult(size=0, perimeter=0, coordinate=None, cells=())

    return RegionResult(
        size=best_size,
        perimeter=best_perimeter,
        coordinate=best_coord,
        cells=best_cells,
    )


def _demo() -> None:
    grid = [
        [5, 5, 1, 9, 9],
        [5, 5, 1, 9, 1],
        [1, 1, 1, 1, 1],
        [8, 8, 1, 3, 3],
        [8, 8, 1, 3, 3],
    ]
    T = 4

    result = largest_region(grid, T)
    print("Grid:")
    for row in grid:
        print(row)
    print(f"Threshold: {T}\n")
    print(f"Largest region size:      {result.size}")
    print(f"Largest region perimeter: {result.perimeter}")
    print(f"Smallest coordinate:      {result.coordinate}")
    print(f"Cells in region:          {sorted(result.cells)}")


if __name__ == "__main__":
    _demo()