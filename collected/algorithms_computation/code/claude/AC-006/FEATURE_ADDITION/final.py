"""
PROBLEM (restated)
-------------------
Given a 2D numeric grid and a threshold T, find the largest 4-connected
region (up/down/left/right adjacency) consisting of cells whose value is
>= T.

ORIGINAL REQUIRED OUTPUTS (unchanged, always present)
------------------------------------------------------
  - size:        number of cells in the region
  - perimeter:   total count of "exposed sides" of the region, where a
                  side of a cell is exposed if the neighbor across that
                  side is either outside the grid or is not part of the
                  region (i.e. its value is < T)
  - coordinate:  the smallest (row, col) coordinate belonging to that
                  region (using standard tuple ordering: compare row
                  first, then column)

Tie-breaking when multiple regions share the maximum size:
  1. Prefer the region with the LARGER perimeter.
  2. If still tied, prefer the region with the SMALLER coordinate
     (smallest (row, col) tuple contained in the region).

If no cell qualifies, the required output is (size=0, perimeter=0,
coordinate=None).

NEW FEATURE (additive, opt-in, off by default)
------------------------------------------------
An additional `operation_summary` field may be requested. When present,
it reports a deterministic count of the "major computational decisions/
operations" the algorithm performed while scanning the grid. This is
pure bookkeeping around the existing algorithm — it does not change
which region is chosen, nor any of the three original output values.

`operation_summary` is a dict with the following deterministic counters:
  - "qualification_checks": how many times a cell was tested against
     the threshold (i.e. calls to the qualifies() predicate — this
     includes checks of the starting cell of each flood fill and every
     neighbor check made during flood fill).
  - "cells_visited":         how many cells were popped off the flood
     fill stack and processed (equals total qualifying cells across all
     regions, since each cell is visited exactly once).
  - "cells_pushed":          how many times a cell was pushed onto the
     flood fill stack (equals cells_visited, since every pushed cell is
     eventually popped exactly once).
  - "neighbor_decisions":    how many times a neighbor of a visited cell
     was examined to decide whether it's an interior connection (same
     region) or an exposed side (contributes to perimeter). This equals
     4 * cells_visited (every cell has exactly 4 sides examined).
  - "region_comparisons":    how many times a newly completed region was
     compared against the current best region using the tie-break rule.
  - "regions_found":         how many distinct qualifying regions were
     discovered in total.
  - "total_operations":      the sum of qualification_checks,
     neighbor_decisions, and region_comparisons — a single deterministic
     scalar summarizing total algorithmic work.

KEY CONSTRAINTS
----------------
- The grid is a rectangular list of lists of numbers (int/float). It may
  be empty, or contain rows of length 0.
- T is a numeric threshold; a cell qualifies if grid[r][c] >= T.
- Connectivity is strictly 4-directional (no diagonals).
- The solution must be fully deterministic: no randomness, no reliance
  on hash-ordering, no network/API access, no external services, and no
  human interaction. Only the Python standard library may be used.
- Flood fill must be implemented iteratively (explicit stack), not via
  recursion, to avoid recursion-depth issues on large grids and to keep
  behavior deterministic and reproducible.
- BACKWARD COMPATIBILITY: when the new feature is disabled (default) or
  not requested, the function's return shape and every original field's
  value are completely unchanged from the original solution.

REQUIRED OUTPUT
----------------
Default call `largest_threshold_region(grid, T)`:
    -> (size, perimeter, coordinate)                [unchanged]

Opt-in call `largest_threshold_region(grid, T, include_operation_summary=True)`:
    -> (size, perimeter, coordinate, operation_summary)

ALGORITHM
---------
1. Scan the grid in row-major order. Skip cells that are already visited
   or that don't meet the threshold (each such test is a
   "qualification_checks" operation).
2. For every unvisited qualifying cell, run an iterative flood fill
   (DFS using an explicit stack) to discover the full connected region:
     - Mark cells visited as they are pushed ("cells_pushed"), to avoid
       duplicate work.
     - For each cell popped ("cells_visited"), examine its 4 neighbors
       ("neighbor_decisions"):
         * If the neighbor is in-bounds AND qualifies (>= T), it's part
           of the same region -> push it if not already visited.
         * Otherwise (out-of-bounds OR value < T), that side of the
           current cell is "exposed" -> increment the perimeter counter.
   This guarantees every exposed side is counted exactly once, matching
   the standard "area/perimeter of a polyomino" definition.
3. After the region is fully explored, compute its size (cell count) and
   its minimal coordinate (min of all (row, col) pairs in the region).
4. Compare ("region_comparisons") against the best region found so far
   using the tie-break rules (bigger size > bigger perimeter > smaller
   coordinate) and keep the winner.
5. Return the best region's stats after scanning the whole grid, plus
   the operation summary if requested.

Because each cell is visited at most once (via the `visited` matrix) and
each edge is inspected a constant number of times, the algorithm runs in
O(rows * cols) time and space, and so does operation counting.
"""

from typing import Dict, List, Optional, Tuple, Union

Number = Union[int, float]
Grid = List[List[Number]]


def largest_threshold_region(
    grid: Grid,
    threshold: Number,
    include_operation_summary: bool = False,
) -> Union[
    Tuple[int, int, Optional[Tuple[int, int]]],
    Tuple[int, int, Optional[Tuple[int, int]], Dict[str, int]],
]:
    """
    Find the largest 4-connected region of cells with value >= threshold.

    Default behavior (include_operation_summary=False, the default):
        Returns (size, perimeter, smallest_coordinate) -- IDENTICAL to
        the original implementation in every respect.

    Opt-in behavior (include_operation_summary=True):
        Returns (size, perimeter, smallest_coordinate, operation_summary)
        where operation_summary is a dict of deterministic operation
        counts as described in the module docstring. The first three
        values are guaranteed identical to the default-mode output for
        the same grid/threshold.
    """
    # Operation counters (only meaningful/used if include_operation_summary).
    qualification_checks = 0
    cells_visited = 0
    cells_pushed = 0
    neighbor_decisions = 0
    region_comparisons = 0
    regions_found = 0

    def empty_result():
        if include_operation_summary:
            summary = {
                "qualification_checks": 0,
                "cells_visited": 0,
                "cells_pushed": 0,
                "neighbor_decisions": 0,
                "region_comparisons": 0,
                "regions_found": 0,
                "total_operations": 0,
            }
            return (0, 0, None, summary)
        return (0, 0, None)

    if not grid or not grid[0]:
        return empty_result()

    rows = len(grid)
    cols = len(grid[0])
    visited = [[False] * cols for _ in range(rows)]

    def qualifies(r: int, c: int) -> bool:
        nonlocal qualification_checks
        qualification_checks += 1
        return 0 <= r < rows and 0 <= c < cols and grid[r][c] >= threshold

    def better(candidate, current) -> bool:
        """True if `candidate` should replace `current` as the best region."""
        c_size, c_perim, c_coord = candidate
        b_size, b_perim, b_coord = current
        if c_size != b_size:
            return c_size > b_size
        if c_perim != b_perim:
            return c_perim > b_perim
        return c_coord < b_coord

    best: Optional[Tuple[int, int, Tuple[int, int]]] = None

    DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for r in range(rows):
        for c in range(cols):
            if visited[r][c] or not qualifies(r, c):
                continue

            # Iterative flood fill (explicit stack, no recursion).
            stack = [(r, c)]
            visited[r][c] = True
            cells_pushed += 1
            size = 0
            perimeter = 0
            min_coord = (r, c)

            while stack:
                cr, cc = stack.pop()
                cells_visited += 1
                size += 1
                if (cr, cc) < min_coord:
                    min_coord = (cr, cc)

                for dr, dc in DIRECTIONS:
                    neighbor_decisions += 1
                    nr, nc = cr + dr, cc + dc
                    if qualifies(nr, nc):
                        if not visited[nr][nc]:
                            visited[nr][nc] = True
                            cells_pushed += 1
                            stack.append((nr, nc))
                        # If it qualifies but is already visited, it's
                        # still part of the region (interior edge), so
                        # it is NOT an exposed side.
                    else:
                        # Out of bounds or below threshold -> exposed side.
                        perimeter += 1

            regions_found += 1
            candidate = (size, perimeter, min_coord)
            region_comparisons += 1
            if best is None or better(candidate, best):
                best = candidate

    if best is None:
        return empty_result()

    if not include_operation_summary:
        return best

    total_operations = (
        qualification_checks + neighbor_decisions + region_comparisons
    )
    operation_summary = {
        "qualification_checks": qualification_checks,
        "cells_visited": cells_visited,
        "cells_pushed": cells_pushed,
        "neighbor_decisions": neighbor_decisions,
        "region_comparisons": region_comparisons,
        "regions_found": regions_found,
        "total_operations": total_operations,
    }
    return best + (operation_summary,)


def _self_test() -> None:
    """Deterministic sanity checks for both the original and new behavior."""
    grid1 = [
        [5, 5, 1, 3],
        [5, 5, 1, 4],
        [1, 1, 1, 4],
        [2, 4, 4, 4],
    ]

    # --- Original behavior must be unchanged ---
    result = largest_threshold_region(grid1, 4)
    print("Test 1 (default, unchanged shape):", result)
    assert len(result) == 3
    assert result[0] == 5  # size of the 4-region (L shape)

    grid2 = [
        [1, 1],
        [1, 1],
    ]
    result2 = largest_threshold_region(grid2, 10)
    print("Test 2 (default, empty):", result2)
    assert result2 == (0, 0, None)

    grid3 = [[7]]
    result3 = largest_threshold_region(grid3, 7)
    print("Test 3 (default, single cell):", result3)
    assert result3 == (1, 4, (0, 0))

    grid4 = [
        [9, 9, 0, 9, 9],
        [9, 9, 0, 0, 9],
    ]
    result4 = largest_threshold_region(grid4, 9)
    print("Test 4 (default, tie-break by size):", result4)
    assert result4[0] == 4

    # --- New feature: opt-in operation_summary ---
    full1 = largest_threshold_region(grid1, 4, include_operation_summary=True)
    print("Test 5 (with operation_summary):", full1)
    assert len(full1) == 4
    size, perimeter, coord, summary = full1
    # First three fields must match the default-mode call exactly.
    assert (size, perimeter, coord) == result
    assert summary["total_operations"] == (
        summary["qualification_checks"]
        + summary["neighbor_decisions"]
        + summary["region_comparisons"]
    )
    assert summary["cells_pushed"] == summary["cells_visited"]
    assert summary["neighbor_decisions"] == 4 * summary["cells_visited"]

    # Empty grid with summary requested.
    empty_full = largest_threshold_region([], 1, include_operation_summary=True)
    print("Test 6 (empty grid, with operation_summary):", empty_full)
    assert empty_full == (
        0,
        0,
        None,
        {
            "qualification_checks": 0,
            "cells_visited": 0,
            "cells_pushed": 0,
            "neighbor_decisions": 0,
            "region_comparisons": 0,
            "regions_found": 0,
            "total_operations": 0,
        },
    )

    # No qualifying cells, with summary requested.
    no_match_full = largest_threshold_region(grid2, 10, include_operation_summary=True)
    print("Test 7 (no match, with operation_summary):", no_match_full)
    assert no_match_full[:3] == (0, 0, None)
    assert no_match_full[3]["regions_found"] == 0

    print("All self-tests passed.")


if __name__ == "__main__":
    _self_test()

    # Example usage: original behavior (unchanged).
    example_grid = [
        [3, 4, 4, 1],
        [4, 4, 1, 1],
        [1, 1, 5, 5],
        [1, 1, 5, 5],
    ]
    T = 4
    size, perimeter, coord = largest_threshold_region(example_grid, T)
    print(f"\nGrid: {example_grid}\nThreshold: {T}")
    print(f"[default] size={size}, perimeter={perimeter}, smallest_coord={coord}")

    # Example usage: new opt-in feature.
    size2, perimeter2, coord2, summary = largest_threshold_region(
        example_grid, T, include_operation_summary=True
    )
    print(
        f"[with summary] size={size2}, perimeter={perimeter2}, "
        f"smallest_coord={coord2}, operation_summary={summary}"
    )