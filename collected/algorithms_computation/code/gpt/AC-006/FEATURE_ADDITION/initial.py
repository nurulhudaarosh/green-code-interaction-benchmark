from typing import Sequence, Tuple, Optional

Coordinate = Tuple[int, int]
Result = Tuple[int, int, Coordinate]


def largest_threshold_region(
    grid: Sequence[Sequence[float]],
    T: float
) -> Result:
    """
    Find the largest 4-connected region of cells with value >= T.

    Returns:
        (size, perimeter, smallest_coordinate)

    Tie-breaking:
        1. Larger size
        2. Larger perimeter
        3. Smaller coordinate (row, column)

    Uses iterative flood fill and counts every exposed side.
    """

    # Handle empty grid.
    if not grid:
        return (0, 0, (-1, -1))

    rows = len(grid)

    # Treat a grid with zero columns as empty.
    cols = len(grid[0])
    if cols == 0:
        return (0, 0, (-1, -1))

    # Validate that the grid is rectangular.
    for row in grid:
        if len(row) != cols:
            raise ValueError("grid must be rectangular")

    visited = [[False] * cols for _ in range(rows)]

    directions = (
        (-1, 0),  # up
        (1, 0),   # down
        (0, -1),  # left
        (0, 1),   # right
    )

    best_size = 0
    best_perimeter = 0
    best_coordinate: Optional[Coordinate] = None

    for r in range(rows):
        for c in range(cols):

            # Skip cells that cannot belong to a region.
            if visited[r][c] or grid[r][c] < T:
                continue

            # Start a new region.
            stack = [(r, c)]
            visited[r][c] = True

            size = 0
            perimeter = 0
            smallest = (r, c)

            while stack:
                cr, cc = stack.pop()

                size += 1
                smallest = min(smallest, (cr, cc))

                # Examine all four sides.
                for dr, dc in directions:
                    nr = cr + dr
                    nc = cc + dc

                    # Outside the grid => exposed side.
                    if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                        perimeter += 1
                        continue

                    # Neighbor does not belong to this region.
                    if grid[nr][nc] < T:
                        perimeter += 1
                        continue

                    # Qualifying neighbor: visit it once.
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            # Compare this region against the current best.
            better = (
                size > best_size
                or (
                    size == best_size
                    and perimeter > best_perimeter
                )
                or (
                    size == best_size
                    and perimeter == best_perimeter
                    and (
                        best_coordinate is None
                        or smallest < best_coordinate
                    )
                )
            )

            if better:
                best_size = size
                best_perimeter = perimeter
                best_coordinate = smallest

    # No qualifying region.
    if best_coordinate is None:
        return (0, 0, (-1, -1))

    return (best_size, best_perimeter, best_coordinate)


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def _run_tests() -> None:
    # Single cell.
    assert largest_threshold_region(
        [[5]],
        5
    ) == (1, 4, (0, 0))

    # Two horizontally connected cells.
    assert largest_threshold_region(
        [[5, 5]],
        5
    ) == (2, 6, (0, 0))

    # 2x2 block.
    assert largest_threshold_region(
        [[5, 5],
         [5, 5]],
        5
    ) == (4, 8, (0, 0))

    # Diagonal cells are NOT connected.
    assert largest_threshold_region(
        [[5, 0],
         [0, 5]],
        5
    ) == (1, 4, (0, 0))

    # Two regions with equal size and perimeter:
    # smaller coordinate wins.
    assert largest_threshold_region(
        [[5, 0, 5],
         [5, 0, 5]],
        5
    ) == (2, 6, (0, 0))

    # Equal size, different perimeter:
    # larger perimeter wins.
    grid = [
        [5, 5, 0, 5],
        [5, 0, 0, 5],
        [0, 0, 0, 5],
    ]

    # Left region: 3 cells, perimeter 8.
    # Right region: 3 cells, perimeter 8.
    # Same size/perimeter -> (0,0) wins.
    assert largest_threshold_region(grid, 5) == (3, 8, (0, 0))

    # No qualifying cells.
    assert largest_threshold_region(
        [[1, 2],
         [2, 1]],
        5
    ) == (0, 0, (-1, -1))

    # Empty grid.
    assert largest_threshold_region([], 5) == (0, 0, (-1, -1))

    # Empty rows.
    assert largest_threshold_region([[]], 5) == (0, 0, (-1, -1))

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()