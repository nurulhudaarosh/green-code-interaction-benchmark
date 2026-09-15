from typing import List, Optional, Tuple

Coordinate = Tuple[int, int]
Result = Tuple[int, int, Optional[Coordinate]]


def largest_region(grid: List[List[int]], T: int) -> Result:
    """
    Find the largest 4-connected region of cells with value >= T.

    Tie-breaking:
        1. Larger region size
        2. Larger perimeter
        3. Smaller lexicographic coordinate (row, column)

    Returns:
        (size, perimeter, smallest_coordinate)

    For an empty grid or no qualifying cells:
        (0, 0, None)
    """

    if not grid or not grid[0]:
        return (0, 0, None)

    rows = len(grid)
    cols = len(grid[0])

    # Assumes the grid is rectangular.
    # Validate this explicitly for deterministic behavior.
    if any(len(row) != cols for row in grid):
        raise ValueError("grid must be rectangular")

    visited = [[False] * cols for _ in range(rows)]

    # Up, down, left, right
    directions = (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    )

    best_size = 0
    best_perimeter = 0
    best_coordinate = None

    for start_r in range(rows):
        for start_c in range(cols):
            # Skip cells that cannot belong to a region.
            if visited[start_r][start_c] or grid[start_r][start_c] < T:
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

                    # Outside the grid => exposed side.
                    if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                        perimeter += 1
                        continue

                    # Neighbor is below threshold => exposed side.
                    if grid[nr][nc] < T:
                        perimeter += 1
                        continue

                    # Qualifying neighbor => part of the same region.
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            # Apply the required tie-breaking rules.
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


# ------------------------------------------------------------
# Example tests
# ------------------------------------------------------------

if __name__ == "__main__":
    grid = [
        [5, 5, 1, 2],
        [5, 4, 1, 2],
        [1, 4, 4, 2],
        [3, 1, 2, 2],
    ]

    T = 4

    print(largest_region(grid, T))
    # Expected:
    # (5, 10, (0, 0))

    # Two regions with equal size/perimeter:
    # the lexicographically smaller coordinate wins.
    grid2 = [
        [5, 1, 5],
        [5, 1, 5],
    ]

    print(largest_region(grid2, 5))
    # Both regions have size 2 and perimeter 6.
    # Left region starts at (0, 0), so it wins.
    # Expected:
    # (2, 6, (0, 0))

    # No qualifying cells.
    grid3 = [
        [1, 2],
        [2, 3],
    ]

    print(largest_region(grid3, 5))
    # Expected:
    # (0, 0, None)