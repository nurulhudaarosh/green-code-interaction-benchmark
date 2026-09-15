from typing import List, Optional, Tuple, NamedTuple


class RegionResult(NamedTuple):
    size: int
    perimeter: int
    top_left: Optional[Tuple[int, int]]  # smallest (row, col) in the region; None if no region


def largest_region(grid: List[List[float]], T: float) -> RegionResult:
    """
    Find the largest 4-connected region of cells with value >= T.

    Tie-breaking order among candidate regions:
        1. larger size wins
        2. then larger perimeter wins
        3. then smaller (row, col) coordinate wins

    Returns RegionResult(size, perimeter, top_left).
    If no cell qualifies, returns RegionResult(0, 0, None).
    """
    if not grid or not grid[0]:
        return RegionResult(0, 0, None)

    n_rows = len(grid)
    n_cols = len(grid[0])
    for row in grid:
        if len(row) != n_cols:
            raise ValueError("grid must be rectangular (all rows same length)")

    def qualifies(r: int, c: int) -> bool:
        return grid[r][c] >= T

    visited = [[False] * n_cols for _ in range(n_rows)]
    best_key = None
    best_result = RegionResult(0, 0, None)
    DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for r0 in range(n_rows):
        for c0 in range(n_cols):
            if visited[r0][c0] or not qualifies(r0, c0):
                continue

            top_left = (r0, c0)          # smallest coord of this region, guaranteed by scan order
            visited[r0][c0] = True
            stack = [(r0, c0)]
            size = 0
            perimeter = 0

            while stack:
                r, c = stack.pop()
                size += 1
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if nr < 0 or nr >= n_rows or nc < 0 or nc >= n_cols:
                        perimeter += 1
                        continue
                    if not qualifies(nr, nc):
                        perimeter += 1
                        continue
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            key = (-size, -perimeter, top_left)
            if best_key is None or key < best_key:
                best_key = key
                best_result = RegionResult(size, perimeter, top_left)

    return best_result