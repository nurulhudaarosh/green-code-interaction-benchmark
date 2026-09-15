from typing import List, Optional, Tuple

Coordinate = Tuple[int, int]
Result = Tuple[int, int, Optional[Coordinate]]


def largest_threshold_region(
    grid: List[List[float]],
    T: float
) -> Result:
    """
    Find the largest 4-connected region containing cells with value >= T.

    Returns:
        (size, perimeter, smallest_coordinate)

    Tie-breaking:
        1. Larger region size.
        2. Larger perimeter.
        3. Smaller lexicographical coordinate (row, column).

    For an empty grid or no qualifying cells:
        (0, 0, None)
    """

    if not grid:
        return (0, 0, None)

    rows = len(grid)

    # Treat the grid as potentially rectangular. A valid input is expected
    # to have equal row lengths.
    cols = len(grid[0])

    if cols == 0:
        return (0, 0, None)

    # Validate rectangular shape.
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
    best_coordinate = None

    for r in range(rows):
        for c in range(cols):
            # Skip cells that cannot belong to a region or were already
            # included in another region.
            if visited[r][c] or grid[r][c] < T:
                continue

            # Iterative flood fill.
            stack = [(r, c)]
            visited[r][c] = True

            size = 0
            perimeter = 0
            smallest_coordinate = (r, c)

            while stack:
                cr, cc = stack.pop()
                size += 1

                if (cr, cc) < smallest_coordinate:
                    smallest_coordinate = (cr, cc)

                for dr, dc in directions:
                    nr = cr + dr
                    nc = cc + dc

                    # Outside the grid => exposed side.
                    if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                        perimeter += 1
                        continue

                    # Neighbor below threshold => exposed side.
                    if grid[nr][nc] < T:
                        perimeter += 1
                        continue

                    # Eligible neighbor not yet visited.
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            # Apply deterministic tie-breaking.
            is_better = (
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
                        or smallest_coordinate < best_coordinate
                    )
                )
            )

            if is_better:
                best_size = size
                best_perimeter = perimeter
                best_coordinate = smallest_coordinate

    return (best_size, best_perimeter, best_coordinate)


if __name__ == "__main__":
    grid = [
        [5, 5, 1, 2],
        [5, 4, 1, 2],
        [1, 4, 4, 2],
        [3, 1, 2, 2],
    ]

    T = 4

    print(largest_threshold_region(grid, T))