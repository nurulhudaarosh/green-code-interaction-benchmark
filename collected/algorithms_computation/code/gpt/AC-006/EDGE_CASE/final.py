from typing import List, Optional, Tuple

Coordinate = Tuple[int, int]
Result = Tuple[int, int, Optional[Coordinate]]


def largest_threshold_region(
    grid: List[List[float]],
    T: float
) -> Result:
    """
    Find the largest 4-connected region of cells whose value >= T.

    Returns:
        (size, perimeter, smallest_coordinate)

    Tie-breaking:
        1. Larger size
        2. Larger perimeter
        3. Smaller lexicographical coordinate (row, column)

    Empty grid / no qualifying cells:
        (0, 0, None)
    """

    if not grid:
        return (0, 0, None)

    rows = len(grid)
    cols = len(grid[0])

    if cols == 0:
        return (0, 0, None)

    if any(len(row) != cols for row in grid):
        raise ValueError("grid must be rectangular")

    visited = [[False] * cols for _ in range(rows)]

    directions = (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
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

                if (cr, cc) < smallest_coordinate:
                    smallest_coordinate = (cr, cc)

                for dr, dc in directions:
                    nr = cr + dr
                    nc = cc + dc

                    # Grid boundary -> exposed side.
                    if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                        perimeter += 1
                        continue

                    # Below threshold -> exposed side.
                    if grid[nr][nc] < T:
                        perimeter += 1
                        continue

                    # Qualifying and not visited -> same region.
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            # Deterministic tie-breaking:
            # size > perimeter > coordinate.
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

    return best_size, best_perimeter, best_coordinate


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def run_tests():
    # 1. Basic region.
    grid = [
        [5, 5, 1],
        [5, 1, 1],
        [1, 1, 4],
    ]
    assert largest_threshold_region(grid, 4) == (3, 8, (0, 0))

    # 2. Repeated values:
    # All 5s are qualifying, and because they are connected,
    # they must form ONE region rather than separate regions.
    grid = [
        [5, 5, 5],
        [5, 5, 5],
        [1, 1, 1],
    ]
    assert largest_threshold_region(grid, 5) == (6, 10, (0, 0))

    # 3. Repeated values but disconnected:
    # Equal values in separate components remain separate regions.
    grid = [
        [5, 1, 5],
        [1, 1, 1],
        [5, 1, 5],
    ]

    # Four separate single-cell regions.
    # All have size 1 and perimeter 4.
    # Deterministic coordinate tie-breaking selects (0, 0).
    assert largest_threshold_region(grid, 5) == (1, 4, (0, 0))

    # 4. Equal size, different perimeter:
    # The region on the left has size 3 and perimeter 8.
    # The region on the right has size 3 and perimeter 8 here,
    # so coordinate tie-breaking is used.
    grid = [
        [5, 5, 1, 5],
        [5, 1, 1, 5],
        [1, 1, 1, 5],
    ]
    assert largest_threshold_region(grid, 5) == (3, 8, (0, 0))

    # 5. Deterministic coordinate tie:
    # Two disconnected 2-cell regions, both with size 2
    # and perimeter 6. The region beginning at (0, 0) wins.
    grid = [
        [5, 5, 1, 5],
        [1, 1, 1, 5],
    ]
    assert largest_threshold_region(grid, 5) == (2, 6, (0, 0))

    # 6. Repeated values at the threshold are INCLUDED.
    grid = [
        [4, 4, 1],
        [1, 4, 1],
        [1, 1, 1],
    ]
    assert largest_threshold_region(grid, 4) == (3, 8, (0, 0))

    # 7. Values below threshold are excluded.
    grid = [
        [3, 3],
        [3, 2],
    ]
    assert largest_threshold_region(grid, 3) == (3, 8, (0, 0))

    # 8. No qualifying cells.
    grid = [
        [1, 2],
        [2, 1],
    ]
    assert largest_threshold_region(grid, 3) == (0, 0, None)

    # 9. Empty grid.
    assert largest_threshold_region([], 5) == (0, 0, None)

    # 10. Single qualifying cell.
    grid = [
        [1, 5, 1],
    ]
    assert largest_threshold_region(grid, 5) == (1, 4, (0, 1))

    # 11. Equal size and perimeter, later region must NOT replace
    # the earlier coordinate.
    grid = [
        [5, 1, 5],
        [1, 1, 1],
    ]
    assert largest_threshold_region(grid, 5) == (1, 4, (0, 0))

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()