from typing import List, Optional, Tuple

Coordinate = Tuple[int, int]
Result = Tuple[int, int, Optional[Coordinate]]


def largest_threshold_region(grid: List[List[int]], T: int) -> Result:
    """
    Return the largest 4-connected region of cells with value >= T.

    Result:
        (size, perimeter, smallest_coordinate)

    Tie-breaking:
        1. Larger size
        2. Larger perimeter
        3. Smaller lexicographic coordinate (row, column)

    If no qualifying cells exist:
        (0, 0, None)
    """

    if not grid or not grid[0]:
        return (0, 0, None)

    rows = len(grid)
    cols = len(grid[0])

    if any(len(row) != cols for row in grid):
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
                smallest_coordinate = min(
                    smallest_coordinate,
                    (cr, cc)
                )

                for dr, dc in directions:
                    nr = cr + dr
                    nc = cc + dc

                    # Outside the grid -> exposed side.
                    if not (0 <= nr < rows and 0 <= nc < cols):
                        perimeter += 1
                        continue

                    # Below threshold -> exposed side.
                    if grid[nr][nc] < T:
                        perimeter += 1
                        continue

                    # Qualifying neighbor -> same region.
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            # Deterministic comparison:
            # size DESC, perimeter DESC, coordinate ASC.
            if (
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
            ):
                best_size = size
                best_perimeter = perimeter
                best_coordinate = smallest_coordinate

    return (best_size, best_perimeter, best_coordinate)


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

if __name__ == "__main__":
    # Test 1: Correct size and perimeter.
    grid1 = [
        [5, 5, 1],
        [5, 4, 1],
        [1, 4, 4],
    ]

    assert largest_threshold_region(grid1, 4) == (
        7, 12, (0, 0)
    )

    # Test 2: Equal size + equal perimeter.
    # The lexicographically smallest coordinate must win.
    grid2 = [
        [5, 5, 1, 5, 5],
        [1, 1, 1, 1, 1],
        [5, 5, 1, 5, 5],
    ]

    assert largest_threshold_region(grid2, 5) == (
        2, 6, (0, 0)
    )

    # Test 3: No qualifying cells.
    grid3 = [
        [1, 2],
        [2, 3],
    ]

    assert largest_threshold_region(grid3, 5) == (
        0, 0, None
    )

    # Test 4: Single cell.
    # Four sides are exposed.
    grid4 = [
        [1, 5, 1],
    ]

    assert largest_threshold_region(grid4, 5) == (
        1, 4, (0, 1)
    )

    print("All tests passed.")