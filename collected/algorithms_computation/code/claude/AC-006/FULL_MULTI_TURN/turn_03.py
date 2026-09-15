"""
Largest 4-connected region (value >= T) finder.
Deterministic, standard-library-only. Iterative flood fill; counts every exposed side.

Feature: optional `operation_summary` reporting major computational decisions made
by the algorithm, without altering any original field/behavior when not requested.
"""

from typing import Dict, List, NamedTuple, Optional, Tuple


class RegionResult(NamedTuple):
    size: int
    perimeter: int
    coordinate: Optional[Tuple[int, int]]
    cells: Tuple[Tuple[int, int], ...]
    operation_summary: Optional[Dict[str, int]] = None  # None unless explicitly requested


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
    ops: Dict[str, int],
) -> Tuple[int, int, Tuple[int, int], List[Tuple[int, int]]]:
    """
    Iterative (stack-based) flood fill. Every "major operation" tallied in `ops`:
      - cells_visited: one per cell popped/processed
      - neighbor_checks: one per neighbor examined (in/out of bounds, below/above threshold)
      - exposed_sides_counted: one per side determined to be exposed (== perimeter contributions)
      - cells_pushed: one per new cell added to the exploration stack
    """
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
        ops["cells_visited"] += 1
        cells.append((r, c))
        if (r, c) < smallest:
            smallest = (r, c)

        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            ops["neighbor_checks"] += 1

            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                perimeter += 1
                ops["exposed_sides_counted"] += 1
                continue
            if grid[nr][nc] < threshold:
                perimeter += 1
                ops["exposed_sides_counted"] += 1
                continue
            if not visited[nr][nc]:
                visited[nr][nc] = True
                stack.append((nr, nc))
                ops["cells_pushed"] += 1
            # else: internal shared edge to an already-visited in-region cell -> no operation tallied
            # beyond the neighbor_check already counted above (still a decision point).

    return size, perimeter, smallest, cells


def _region_key(size: int, perimeter: int, coord: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """
    Explicit sort key enforcing the tie-break rule:
      1) larger size wins
      2) larger perimeter wins
      3) smaller coordinate wins
    """
    return (-size, -perimeter, coord[0], coord[1])


def largest_region(
    grid: List[List[float]],
    threshold: float,
    include_operation_summary: bool = False,
) -> RegionResult:
    """
    Find the largest 4-connected region of cells with value >= threshold.

    All original fields and behavior are unchanged regardless of `include_operation_summary`.
    When `include_operation_summary` is False (default), `operation_summary` is None and
    every other output matches the prior implementation exactly.
    When True, `operation_summary` reports deterministic counts of the algorithm's
    major computational decisions/operations.
    """
    rows, cols = _validate_grid(grid)
    if rows == 0 or cols == 0:
        return RegionResult(
            size=0,
            perimeter=0,
            coordinate=None,
            cells=(),
            operation_summary=(
                {
                    "regions_discovered": 0,
                    "cells_visited": 0,
                    "neighbor_checks": 0,
                    "exposed_sides_counted": 0,
                    "cells_pushed": 0,
                    "tie_break_comparisons": 0,
                    "total_operations": 0,
                }
                if include_operation_summary
                else None
            ),
        )

    visited = [[False] * cols for _ in range(rows)]

    best_key: Optional[Tuple[int, int, int, int]] = None
    best_size = 0
    best_perimeter = 0
    best_coord: Optional[Tuple[int, int]] = None
    best_cells: Tuple[Tuple[int, int], ...] = ()

    # Running operation tallies (always computed internally; only reported if requested,
    # so tracking them never changes core algorithm behavior or results).
    ops: Dict[str, int] = {
        "regions_discovered": 0,
        "cells_visited": 0,
        "neighbor_checks": 0,
        "exposed_sides_counted": 0,
        "cells_pushed": 0,
        "tie_break_comparisons": 0,
    }

    for r in range(rows):
        for c in range(cols):
            if visited[r][c] or grid[r][c] < threshold:
                continue

            ops["regions_discovered"] += 1
            size, perimeter, coord, cells = _flood_fill(
                grid, visited, (r, c), threshold, rows, cols, ops
            )
            key = _region_key(size, perimeter, coord)

            ops["tie_break_comparisons"] += 1  # one decision: is this region better than current best?
            if best_key is None or key < best_key:
                best_key = key
                best_size = size
                best_perimeter = perimeter
                best_coord = coord
                best_cells = tuple(cells)

    if best_coord is None:
        return RegionResult(
            size=0,
            perimeter=0,
            coordinate=None,
            cells=(),
            operation_summary=(
                {**ops, "total_operations": sum(ops.values())}
                if include_operation_summary
                else None
            ),
        )

    return RegionResult(
        size=best_size,
        perimeter=best_perimeter,
        coordinate=best_coord,
        cells=best_cells,
        operation_summary=(
            {**ops, "total_operations": sum(ops.values())}
            if include_operation_summary
            else None
        ),
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

    print("Grid:")
    for row in grid:
        print(row)
    print(f"Threshold: {T}\n")

    # Feature disabled (default): identical to original behavior.
    result_plain = largest_region(grid, T)
    print("-- Feature disabled (default) --")
    print(f"size:              {result_plain.size}")
    print(f"perimeter:         {result_plain.perimeter}")
    print(f"coordinate:        {result_plain.coordinate}")
    print(f"cells:             {sorted(result_plain.cells)}")
    print(f"operation_summary: {result_plain.operation_summary}")  # must be None

    # Feature enabled: adds operation_summary, all other fields identical.
    result_with_ops = largest_region(grid, T, include_operation_summary=True)
    print("\n-- Feature enabled --")
    print(f"size:              {result_with_ops.size}")
    print(f"perimeter:         {result_with_ops.perimeter}")
    print(f"coordinate:        {result_with_ops.coordinate}")
    print(f"cells:             {sorted(result_with_ops.cells)}")
    print(f"operation_summary: {result_with_ops.operation_summary}")

    assert result_plain.size == result_with_ops.size
    assert result_plain.perimeter == result_with_ops.perimeter
    assert result_plain.coordinate == result_with_ops.coordinate
    assert result_plain.cells == result_with_ops.cells
    assert result_plain.operation_summary is None
    assert result_with_ops.operation_summary is not None


if __name__ == "__main__":
    _demo()