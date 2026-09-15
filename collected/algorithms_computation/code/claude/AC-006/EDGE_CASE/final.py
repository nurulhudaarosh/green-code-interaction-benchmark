from typing import List, Optional, Tuple, NamedTuple


class RegionResult(NamedTuple):
    size: int
    perimeter: int
    top_left: Optional[Tuple[int, int]]  # smallest (row, col) in the region; None if no region


def largest_region(grid: List[List[float]], T: float) -> RegionResult:
    """
    Find the largest 4-connected region of cells with value >= T.

    Tie-breaking order among candidate regions:
        1. larger size wins
        2. then larger perimeter wins
        3. then smaller (row, col) coordinate wins

    Returns RegionResult(size, perimeter, top_left).
    If no cell qualifies, returns RegionResult(0, 0, None).

    Deterministic: single row-major pass, iterative flood fill (explicit stack),
    no randomness, no reliance on hash/set ordering for the result.
    Region membership depends only on spatial adjacency and the >= T test,
    never on value equality, so repeated/duplicate values across separate
    regions cannot cause incorrect merging.
    """
    if not grid or not grid[0]:
        return RegionResult(0, 0, None)

    n_rows = len(grid)
    n_cols = len(grid[0])
    for row in grid:
        if len(row) != n_cols:
            raise ValueError("grid must be rectangular (all rows same length)")

    def qualifies(r: int, c: int) -> bool:
        return grid[r][c] >= T

    visited = [[False] * n_cols for _ in range(n_rows)]

    best_key = None          # sort key: (-size, -perimeter, (row, col))
    best_result = RegionResult(0, 0, None)

    DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))  # fixed, deterministic order

    for r0 in range(n_rows):
        for c0 in range(n_cols):
            if visited[r0][c0] or not qualifies(r0, c0):
                continue

            # r0, c0 is the smallest coordinate of this (not-yet-seen) region,
            # since row-major scanning guarantees nothing smaller in this
            # region remains unvisited.
            top_left = (r0, c0)
            visited[r0][c0] = True
            stack = [(r0, c0)]
            size = 0
            perimeter = 0

            while stack:
                r, c = stack.pop()
                size += 1
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if nr < 0 or nr >= n_rows or nc < 0 or nc >= n_cols:
                        perimeter += 1  # off-grid edge is exposed
                        continue
                    if not qualifies(nr, nc):
                        perimeter += 1  # neighbor doesn't qualify -> exposed
                        continue
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
                    # else: qualifying, visited neighbor -> internal edge, not exposed

            key = (-size, -perimeter, top_left)
            if best_key is None or key < best_key:
                best_key = key
                best_result = RegionResult(size, perimeter, top_left)

    return best_result


def _run_tests():
    # --- Original baseline tests ---

    grid1 = [
        [5, 5, 1, 3],
        [5, 5, 1, 3],
        [1, 1, 1, 3],
        [4, 4, 4, 4],
    ]
    res = largest_region(grid1, T=3)
    print("Test 1:", res)
    assert res == RegionResult(7, 16, (0, 3))

    grid2 = [[1, 1], [1, 1]]
    res = largest_region(grid2, T=5)
    print("Test 2:", res)
    assert res == RegionResult(0, 0, None)

    grid3 = [
        [9, 0, 9],
        [0, 0, 0],
        [9, 0, 9],
    ]
    res = largest_region(grid3, T=9)
    print("Test 3:", res)
    assert res == RegionResult(1, 4, (0, 0))

    grid4 = [[7]]
    res = largest_region(grid4, T=7)
    print("Test 4:", res)
    assert res == RegionResult(1, 4, (0, 0))

    grid5 = [
        [2, 2, 2],
        [2, 0, 2],
        [2, 2, 2],
    ]
    res = largest_region(grid5, T=2)
    print("Test 5:", res)
    assert res == RegionResult(8, 16, (0, 0))

    # --- Repeated-value cases ---

    # Same value (10) reused across three disconnected regions.
    grid_rep1 = [
        [10, 10,  0, 10, 10, 10],
        [10, 10,  0,  0,  0, 10],
        [ 0,  0,  0,  0,  0,  0],
        [10,  0,  0,  0,  0,  0],
    ]
    # Region A: 2x2 block (0,0)-(1,1) -> size=4, perimeter=8
    # Region B: L-shape (0,3),(0,4),(0,5),(1,5) -> size=4, perimeter=10
    # Region C: single cell (3,0) -> size=1
    res = largest_region(grid_rep1, T=10)
    print("Test 6 (repeated values, disconnected same-value regions):", res)
    assert res == RegionResult(4, 10, (0, 3))

    # Single connected region mixing identical and differing values, all >= T.
    grid_rep2 = [
        [5, 5, 5],
        [5, 100, 5],
        [5, 5, 5],
    ]
    res = largest_region(grid_rep2, T=5)
    print("Test 7 (repeated + differing values, one region):", res)
    assert res == RegionResult(9, 12, (0, 0))

    # --- Deterministic tie cases ---

    # Three regions tied on both size and perimeter -> smallest coordinate wins.
    grid_tie1 = [
        [7, 7, 0, 7, 7],
        [0, 0, 0, 0, 0],
        [0, 7, 7, 0, 0],
    ]
    res = largest_region(grid_tie1, T=7)
    print("Test 8 (three-way tie on size+perimeter):", res)
    assert res == RegionResult(2, 6, (0, 0))

    # Two regions tied on size but differing perimeter; the smaller-perimeter
    # region is encountered FIRST in scan order, proving perimeter (not scan
    # order) breaks the tie.
    grid_tie2 = [
        [9, 9, 0, 0, 0, 0],   # 2x2 block: size=4, perimeter=8
        [9, 9, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 9, 9, 9, 9],   # straight line of 4: size=4, perimeter=10
    ]
    res = largest_region(grid_tie2, T=9)
    print("Test 9 (equal size, perimeter breaks tie despite scan order):", res)
    assert res == RegionResult(4, 10, (3, 2))

    # --- Determinism checks: repeated runs must be identical ---

    results = [largest_region(grid_tie1, T=7) for _ in range(20)]
    assert all(r == results[0] for r in results), "non-deterministic output detected!"
    print("Test 10 (determinism, tie grid, 20 runs):", results[0])

    results2 = [largest_region(grid_rep1, T=10) for _ in range(20)]
    assert all(r == results2[0] for r in results2), "non-deterministic output detected!"
    print("Test 11 (determinism, repeated-value grid, 20 runs):", results2[0])

    print("\nAll tests passed.")


if __name__ == "__main__":
    _run_tests()