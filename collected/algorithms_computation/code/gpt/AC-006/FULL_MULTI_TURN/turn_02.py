from typing import List, Optional, Tuple

Coordinate = Tuple[int, int]
Result = Tuple[int, int, Optional[Coordinate]]


def largest_threshold_region(
    grid: List[List[float]],
    T: float,
) -> Result:
    """
    Find the largest 4-connected region of cells with value >= T.

    Returns exactly:
        (size, perimeter, smallest_coordinate)

    Tie-breaking:
        1. Larger size wins.
        2. If size ties, larger perimeter wins.
        3. If both tie, lexicographically smaller coordinate wins.

    Coordinates are zero-based.

    If the grid is empty or no cell satisfies value >= T:
        (0, 0, None)
    """

    if not grid or not grid[0]:
        return (0, 0, None)

    rows = len(grid)
    cols = len(grid[0])

    # Preserve the existing rectangular-grid requirement.
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
    best_coordinate: Optional[Coordinate] = None

    for start_row in range(rows):
        for start_col in range(cols):
            if visited[start_row][start_col]:
                continue

            if grid[start_row][start_col] < T:
                continue

            # Iterative flood fill.
            stack = [(start_row, start_col)]
            visited[start_row][start_col] = True

            region_size = 0
            region_perimeter = 0
            region_smallest: Coordinate = (start_row, start_col)

            while stack:
                row, col = stack.pop()
                region_size += 1

                # Explicitly maintain the smallest coordinate.
                current_coordinate = (row, col)
                if current_coordinate < region_smallest:
                    region_smallest = current_coordinate

                # Examine all four sides of this cell.
                for d_row, d_col in directions:
                    neighbor_row = row + d_row
                    neighbor_col = col + d_col

                    # Outside the grid: one exposed side.
                    if (
                        neighbor_row < 0
                        or neighbor_row >= rows
                        or neighbor_col < 0
                        or neighbor_col >= cols
                    ):
                        region_perimeter += 1
                        continue

                    # Below threshold: one exposed side.
                    if grid[neighbor_row][neighbor_col] < T:
                        region_perimeter += 1
                        continue

                    # Qualifying unvisited neighbor: continue flood fill.
                    if not visited[neighbor_row][neighbor_col]:
                        visited[neighbor_row][neighbor_col] = True
                        stack.append((neighbor_row, neighbor_col))

            # Deterministic comparison using every required tie-break rule.
            candidate = (
                region_size,
                region_perimeter,
                region_smallest,
            )

            if best_coordinate is None:
                best_size, best_perimeter, best_coordinate = candidate
            elif (
                region_size > best_size
                or (
                    region_size == best_size
                    and region_perimeter > best_perimeter
                )
                or (
                    region_size == best_size
                    and region_perimeter == best_perimeter
                    and region_smallest < best_coordinate
                )
            ):
                best_size, best_perimeter, best_coordinate = candidate

    return (best_size, best_perimeter, best_coordinate)


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def run_tests() -> None:
    # 1. Basic region.
    grid = [
        [5, 5],
        [5, 5],
    ]
    assert largest_threshold_region(grid, 5) == (4, 8, (0, 0))

    # 2. Defect demonstration case:
    # Explicitly verify the smallest coordinate is returned.
    grid = [
        [5, 5, 1],
        [5, 5, 1],
    ]
    assert largest_threshold_region(grid, 5) == (4, 8, (0, 0))

    # 3. Diagonal cells are not connected.
    grid = [
        [5, 1],
        [1, 5],
    ]
    assert largest_threshold_region(grid, 5) == (1, 4, (0, 0))

    # 4. Larger size wins.
    grid = [
        [5, 5, 1],
        [1, 5, 1],
        [1, 1, 5],
    ]
    assert largest_threshold_region(grid, 5) == (3, 8, (0, 0))

    # 5. Equal size: larger perimeter wins.
    #
    # Left region: 2x2 square, size 4, perimeter 8.
    # Right region: vertical line, size 4, perimeter 10.
    grid = [
        [5, 5, 1, 5],
        [5, 5, 1, 5],
        [1, 1, 1, 5],
        [1, 1, 1, 5],
    ]
    assert largest_threshold_region(grid, 5) == (4, 10, (0, 3))

    # 6. Equal size and perimeter: smaller coordinate wins.
    grid = [
        [5, 5, 1, 5, 5],
        [1, 1, 1, 1, 1],
        [5, 5, 1, 5, 5],
    ]
    assert largest_threshold_region(grid, 5) == (2, 6, (0, 0))

    # 7. Repeated values remain valid and deterministic.
    grid = [
        [7, 7, 1],
        [7, 7, 1],
        [1, 1, 7],
    ]
    assert largest_threshold_region(grid, 7) == (4, 8, (0, 0))

    # 8. Every cell equal to the threshold qualifies.
    grid = [
        [5, 5],
        [4, 5],
    ]
    assert largest_threshold_region(grid, 5) == (3, 8, (0, 0))

    # 9. No qualifying cells.
    grid = [
        [1, 2],
        [3, 4],
    ]
    assert largest_threshold_region(grid, 5) == (0, 0, None)

    # 10. Empty grid.
    assert largest_threshold_region([], 5) == (0, 0, None)

    # 11. Empty row.
    assert largest_threshold_region([[]], 5) == (0, 0, None)

    # 12. Non-rectangular grids remain invalid.
    try:
        largest_threshold_region([[5, 5], [5]], 5)
        assert False, "Expected ValueError"
    except ValueError:
        pass

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()