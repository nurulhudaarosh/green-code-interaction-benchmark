from typing import Sequence, Tuple, Optional, Union, Dict, Any

Coordinate = Tuple[int, int]
BasicResult = Tuple[int, int, Coordinate]
ExtendedResult = Tuple[int, int, Coordinate, Dict[str, int]]


def largest_threshold_region(
    grid: Sequence[Sequence[float]],
    T: float,
    include_operation_summary: bool = False,
) -> Union[BasicResult, ExtendedResult]:
    """
    Find the largest 4-connected region of cells with value >= T.

    Original output:
        (size, perimeter, smallest_coordinate)

    Optional extended output:
        (
            size,
            perimeter,
            smallest_coordinate,
            operation_summary
        )

    Tie-breaking:
        1. Larger region size.
        2. Larger perimeter.
        3. Smaller coordinate (row, column).

    operation_summary:
        neighbor_checks = number of four-direction neighbor examinations
                         performed during flood fill.

    The algorithm is deterministic and uses iterative flood fill.
    """

    # ---------------------------------------------------------
    # Empty grid handling
    # ---------------------------------------------------------
    if not grid:
        basic_result = (0, 0, (-1, -1))

        if include_operation_summary:
            return (
                0,
                0,
                (-1, -1),
                {"neighbor_checks": 0},
            )

        return basic_result

    rows = len(grid)

    if len(grid[0]) == 0:
        basic_result = (0, 0, (-1, -1))

        if include_operation_summary:
            return (
                0,
                0,
                (-1, -1),
                {"neighbor_checks": 0},
            )

        return basic_result

    cols = len(grid[0])

    # The algorithm requires a rectangular grid.
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

    # New deterministic operation counter.
    neighbor_checks = 0

    # ---------------------------------------------------------
    # Row-major scan
    # ---------------------------------------------------------
    for r in range(rows):
        for c in range(cols):

            # Ignore already visited or below-threshold cells.
            if visited[r][c] or grid[r][c] < T:
                continue

            # -------------------------------------------------
            # Iterative flood fill
            # -------------------------------------------------
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
                    neighbor_checks += 1

                    nr = cr + dr
                    nc = cc + dc

                    # Outside the grid => exposed side.
                    if (
                        nr < 0
                        or nr >= rows
                        or nc < 0
                        or nc >= cols
                    ):
                        perimeter += 1
                        continue

                    # Below threshold => exposed side.
                    if grid[nr][nc] < T:
                        perimeter += 1
                        continue

                    # Qualifying but not visited => continue flood fill.
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            # -------------------------------------------------
            # Deterministic region comparison
            # -------------------------------------------------
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

    # ---------------------------------------------------------
    # No qualifying region
    # ---------------------------------------------------------
    if best_coordinate is None:
        best_coordinate = (-1, -1)
        best_size = 0
        best_perimeter = 0

    # ---------------------------------------------------------
    # Preserve original output when feature is disabled
    # ---------------------------------------------------------
    if not include_operation_summary:
        return (
            best_size,
            best_perimeter,
            best_coordinate,
        )

    # ---------------------------------------------------------
    # Extended output
    # ---------------------------------------------------------
    operation_summary = {
        "neighbor_checks": neighbor_checks,
    }

    return (
        best_size,
        best_perimeter,
        best_coordinate,
        operation_summary,
    )


# =============================================================
# Tests
# =============================================================

def _run_tests() -> None:

    # ---------------------------------------------------------
    # Original behavior must remain unchanged by default.
    # ---------------------------------------------------------
    assert largest_threshold_region(
        [[5]],
        5
    ) == (1, 4, (0, 0))

    assert largest_threshold_region(
        [[5, 5]],
        5
    ) == (2, 6, (0, 0))

    assert largest_threshold_region(
        [[5, 5],
         [5, 5]],
        5
    ) == (4, 8, (0, 0))

    # Diagonal cells are not connected.
    assert largest_threshold_region(
        [[5, 0],
         [0, 5]],
        5
    ) == (1, 4, (0, 0))

    # No qualifying cells.
    assert largest_threshold_region(
        [[1, 2],
         [2, 1]],
        5
    ) == (0, 0, (-1, -1))

    # Empty grid.
    assert largest_threshold_region([], 5) == (
        0,
        0,
        (-1, -1),
    )

    # Empty row.
    assert largest_threshold_region([[]], 5) == (
        0,
        0,
        (-1, -1),
    )

    # ---------------------------------------------------------
    # Operation summary tests.
    # ---------------------------------------------------------

    # One qualifying cell examines four sides.
    assert largest_threshold_region(
        [[5]],
        5,
        include_operation_summary=True,
    ) == (
        1,
        4,
        (0, 0),
        {"neighbor_checks": 4},
    )

    # Two connected cells examine 4 sides each.
    assert largest_threshold_region(
        [[5, 5]],
        5,
        include_operation_summary=True,
    ) == (
        2,
        6,
        (0, 0),
        {"neighbor_checks": 8},
    )

    # Four-cell block => 4 cells * 4 neighbor checks.
    assert largest_threshold_region(
        [[5, 5],
         [5, 5]],
        5,
        include_operation_summary=True,
    ) == (
        4,
        8,
        (0, 0),
        {"neighbor_checks": 16},
    )

    # Only qualifying cells are flood-filled.
    assert largest_threshold_region(
        [[5, 0],
         [0, 5]],
        5,
        include_operation_summary=True,
    ) == (
        1,
        4,
        (0, 0),
        {"neighbor_checks": 8},
    )

    # No qualifying cells means no flood-fill neighbor checks.
    assert largest_threshold_region(
        [[1, 2],
         [2, 1]],
        5,
        include_operation_summary=True,
    ) == (
        0,
        0,
        (-1, -1),
        {"neighbor_checks": 0},
    )

    # Empty grid.
    assert largest_threshold_region(
        [],
        5,
        include_operation_summary=True,
    ) == (
        0,
        0,
        (-1, -1),
        {"neighbor_checks": 0},
    )

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()