from typing import List, Optional, Tuple

Coordinate = Tuple[int, int]
Result = Tuple[int, int, Optional[Coordinate]]


def largest_threshold_region(
    grid: List[List[float]],
    T: float,
) -> Result:
    """
    Find the largest 4-connected region containing cells with value >= T.

    Returns:
        (size, perimeter, smallest_coordinate)

    Tie-breaking:
        1. Larger size
        2. Larger perimeter
        3. Smaller lexicographical coordinate (row, column)

    For an empty grid or no qualifying cells:
        (0, 0, None)

    Coordinates are zero-based.
    """

    if not grid:
        return (0, 0, None)

    rows = len(grid)

    # Handle an empty first row.
    if not grid[0]:
        return (0, 0, None)

    cols = len(grid[0])

    # Require a rectangular grid.
    for row in grid:
        if len(row) != cols:
            raise ValueError("grid must be rectangular")

    visited = [[False] * cols for _ in range(rows)]

    # Fixed order makes traversal deterministic.
    directions = (
        (-1, 0),  # up
        (1, 0),   # down
        (0, -1),  # left
        (0, 1),   # right
    )

    best_size = 0
    best_perimeter = 0
    best_coordinate = None

    for start_r in range(rows):
        for start_c in range(cols):

            if visited[start_r][start_c]:
                continue

            if grid[start_r][start_c] < T:
                continue

            # Iterative flood fill.
            stack = [(start_r, start_c)]
            visited[start_r][start_c] = True

            size = 0
            perimeter = 0
            smallest_coordinate = (start_r, start_c)

            while stack:
                r, c = stack.pop()

                size += 1

                if (r, c) < smallest_coordinate:
                    smallest_coordinate = (r, c)

                for dr, dc in directions:
                    nr = r + dr
                    nc = c + dc

                    # Outside the grid -> exposed side.
                    if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                        perimeter += 1
                        continue

                    # Neighbor is below threshold -> exposed side.
                    if grid[nr][nc] < T:
                        perimeter += 1
                        continue

                    # Qualifying but not visited -> continue flood fill.
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            # Compare using the required deterministic tie-breaking.
            better = False

            if size > best_size:
                better = True
            elif size == best_size:
                if perimeter > best_perimeter:
                    better = True
                elif perimeter == best_perimeter:
                    if (
                        best_coordinate is None
                        or smallest_coordinate < best_coordinate
                    ):
                        better = True

            if better:
                best_size = size
                best_perimeter = perimeter
                best_coordinate = smallest_coordinate

    return (best_size, best_perimeter, best_coordinate)


# --------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------

def run_tests() -> None:
    # 1. Simple single-cell region.
    grid = [
        [5, 1],
        [1, 1],
    ]
    assert largest_threshold_region(grid, 5) == (1, 4, (0, 0))

    # 2. 2x2 region.
    grid = [
        [5, 5],
        [5, 5],
    ]
    assert largest_threshold_region(grid, 5) == (4, 8, (0, 0))

    # 3. Two regions with different sizes.
    grid = [
        [5, 5, 1],
        [1, 5, 1],
        [1, 1, 5],
    ]
    assert largest_threshold_region(grid, 5) == (3, 8, (0, 0))

    # 4. No qualifying cells.
    grid = [
        [1, 2],
        [3, 4],
    ]
    assert largest_threshold_region(grid, 5) == (0, 0, None)

    # 5. Empty grid.
    assert largest_threshold_region([], 5) == (0, 0, None)

    # 6. Repeated values: all qualifying cells form one region.
    grid = [
        [7, 7, 2],
        [7, 7, 2],
        [2, 2, 7],
    ]
    assert largest_threshold_region(grid, 7) == (4, 8, (0, 0))

    # 7. Equal-size regions: larger perimeter wins.
    #
    # Region A: 2x2 square -> perimeter 8
    # Region B: 1x4 line -> perimeter 10
    #
    # Both have size 4, so Region B wins.
    grid = [
        [5, 5, 1, 5],
        [5, 5, 1, 5],
        [1, 1, 1, 5],
        [1, 1, 1, 5],
    ]
    assert largest_threshold_region(grid, 5) == (4, 10, (0, 3))

    # 8. Equal size and equal perimeter: smallest coordinate wins.
    grid = [
        [5, 5, 1, 5, 5],
        [1, 1, 1, 1, 1],
        [5, 5, 1, 5, 5],
    ]

    # Four separate 2-cell regions, all size 2 and perimeter 6.
    # The top-left region has the smallest coordinate.
    assert largest_threshold_region(grid, 5) == (2, 6, (0, 0))

    # 9. Diagonal cells are NOT connected.
    grid = [
        [5, 1],
        [1, 5],
    ]
    assert largest_threshold_region(grid, 5) == (1, 4, (0, 0))

    # 10. Threshold is inclusive.
    grid = [
        [5, 5],
        [4, 5],
    ]
    assert largest_threshold_region(grid, 5) == (3, 8, (0, 0))

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()