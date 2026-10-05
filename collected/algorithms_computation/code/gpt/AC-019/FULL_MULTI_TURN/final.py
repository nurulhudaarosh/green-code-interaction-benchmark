"""
Minimum-Cost Grid Path

Original problem:
Given a non-negative rectangular cost matrix, move only right or down
from the top-left cell (0, 0) to the bottom-right cell.

Required output:
- The minimum total cost.
- One deterministic optimal path as (row, column) coordinates.

Requirements:
- Use dynamic programming.
- Store predecessor coordinates for path reconstruction.
- Only right/down moves are allowed.
- Deterministic tie handling: if top and left predecessors have equal
  cost, choose the TOP predecessor.
- Preserve the optional operation_summary feature:
    operation_summary=False -> return (minimum_cost, path)
    operation_summary=True  -> return a dictionary containing
                                minimum_cost, path, and operation_summary.
- Use only the standard library.
- No randomness, network access, APIs, external services, or interaction.

Difficult boundary cases explicitly handled:
1. Smallest valid matrix: 1 x 1.
2. Single-row matrix.
3. Single-column matrix.
4. Costs at the largest supported integer boundary.
5. Multiple maximum-boundary costs whose accumulated path cost is
   larger than a single cell value.
6. Tie cases involving boundary values.

Python integers have arbitrary precision, so large valid costs can be
summed without overflow.
"""

from typing import List, Tuple, Union, Dict, Any


def minimum_cost_grid_path(
    cost: List[List[int]],
    operation_summary: bool = False
) -> Union[
    Tuple[int, List[Tuple[int, int]]],
    Dict[str, Any]
]:
    """
    Return the minimum cost and one deterministic optimal path.

    Tie-breaking:
        When the top and left predecessor costs are equal,
        choose the top predecessor.
    """

    # ---------------------------------------------------------
    # Input validation
    # ---------------------------------------------------------
    if not cost:
        raise ValueError("Cost matrix must not be empty.")

    if not cost[0]:
        raise ValueError("Cost matrix must not contain an empty row.")

    rows = len(cost)
    cols = len(cost[0])

    if any(len(row) != cols for row in cost):
        raise ValueError("Cost matrix must be rectangular.")

    if any(value < 0 for row in cost for value in row):
        raise ValueError("All costs must be non-negative.")

    # ---------------------------------------------------------
    # Dynamic programming tables
    # ---------------------------------------------------------
    dp = [[0] * cols for _ in range(rows)]

    # predecessor coordinate for every reachable cell
    parent = [[None] * cols for _ in range(rows)]

    # ---------------------------------------------------------
    # Starting cell
    # ---------------------------------------------------------
    dp[0][0] = cost[0][0]

    # ---------------------------------------------------------
    # First column
    # ---------------------------------------------------------
    # Only a downward move is possible.
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + cost[r][0]
        parent[r][0] = (r - 1, 0)

    # ---------------------------------------------------------
    # First row
    # ---------------------------------------------------------
    # Only a rightward move is possible.
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + cost[0][c]
        parent[0][c] = (0, c - 1)

    # ---------------------------------------------------------
    # Main DP computation
    # ---------------------------------------------------------
    operation_count = 0

    for r in range(1, rows):
        for c in range(1, cols):
            from_top = dp[r - 1][c]
            from_left = dp[r][c - 1]

            operation_count += 1

            # Deterministic tie-breaking:
            # On equality, select the TOP predecessor.
            if from_top <= from_left:
                dp[r][c] = from_top + cost[r][c]
                parent[r][c] = (r - 1, c)
            else:
                dp[r][c] = from_left + cost[r][c]
                parent[r][c] = (r, c - 1)

    # ---------------------------------------------------------
    # Reconstruct path
    # ---------------------------------------------------------
    path = []

    r, c = rows - 1, cols - 1

    while True:
        path.append((r, c))

        if (r, c) == (0, 0):
            break

        r, c = parent[r][c]

    path.reverse()

    minimum_cost = dp[rows - 1][cols - 1]

    # ---------------------------------------------------------
    # Preserve original output when optional feature is disabled
    # ---------------------------------------------------------
    if not operation_summary:
        return minimum_cost, path

    return {
        "minimum_cost": minimum_cost,
        "path": path,
        "operation_summary": {
            "operation_count": operation_count
        }
    }


# =============================================================
# Tests for valid difficult boundary cases
# =============================================================

def run_tests() -> None:

    # ---------------------------------------------------------
    # Test 1: Smallest valid matrix: 1 x 1
    # ---------------------------------------------------------
    cost = [[7]]

    result = minimum_cost_grid_path(cost)

    assert result == (
        7,
        [(0, 0)]
    )

    # No internal DP predecessor decisions exist.
    result = minimum_cost_grid_path(
        cost,
        operation_summary=True
    )

    assert result == {
        "minimum_cost": 7,
        "path": [(0, 0)],
        "operation_summary": {
            "operation_count": 0
        }
    }


    # ---------------------------------------------------------
    # Test 2: Single-row boundary
    # ---------------------------------------------------------
    cost = [[5, 0, 9, 2]]

    result = minimum_cost_grid_path(cost)

    assert result == (
        16,
        [(0, 0), (0, 1), (0, 2), (0, 3)]
    )


    # ---------------------------------------------------------
    # Test 3: Single-column boundary
    # ---------------------------------------------------------
    cost = [
        [5],
        [0],
        [9],
        [2]
    ]

    result = minimum_cost_grid_path(cost)

    assert result == (
        16,
        [(0, 0), (1, 0), (2, 0), (3, 0)]
    )


    # ---------------------------------------------------------
    # Test 4: Zero-cost boundary values
    # ---------------------------------------------------------
    cost = [
        [0, 0],
        [0, 0]
    ]

    result = minimum_cost_grid_path(cost)

    # Both paths cost 0.
    # Tie rule requires choosing the top predecessor.
    assert result == (
        0,
        [(0, 0), (0, 1), (1, 1)]
    )


    # ---------------------------------------------------------
    # Test 5: Very large valid integer boundary
    #
    # Python integers support arbitrary precision, so there is
    # no fixed integer-overflow limit.
    # ---------------------------------------------------------
    MAX_COST = 10**18

    cost = [
        [MAX_COST, MAX_COST],
        [MAX_COST, MAX_COST]
    ]

    result = minimum_cost_grid_path(cost)

    assert result == (
        3 * MAX_COST,
        [(0, 0), (0, 1), (1, 1)]
    )


    # ---------------------------------------------------------
    # Test 6: Large values with a larger accumulated total
    # ---------------------------------------------------------
    MAX_COST = 10**18

    cost = [
        [MAX_COST, MAX_COST, 0],
        [MAX_COST, MAX_COST, 0],
        [0,        0,        0]
    ]

    result = minimum_cost_grid_path(cost)

    assert result == (
        MAX_COST,
        [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
    )


    # ---------------------------------------------------------
    # Test 7: Large boundary values + deterministic tie
    # ---------------------------------------------------------
    MAX_COST = 10**18

    cost = [
        [MAX_COST, 1],
        [1,        1]
    ]

    result = minimum_cost_grid_path(cost)

    # Both routes have the same total:
    # MAX_COST + 1 vs 1 + 1
    #
    # Actually the left route is cheaper, so the result must
    # correctly select it.
    assert result == (
        MAX_COST + 1,
        [(0, 0), (1, 0), (1, 1)]
    )


    # ---------------------------------------------------------
    # Test 8: Exact tie with maximum boundary values
    # ---------------------------------------------------------
    MAX_COST = 10**18

    cost = [
        [MAX_COST, 0],
        [0,        0]
    ]

    result = minimum_cost_grid_path(cost)

    # Both possible paths have the same cost MAX_COST.
    # At (1,1), top and left predecessor costs are equal.
    # Therefore, choose the TOP predecessor.
    assert result == (
        MAX_COST,
        [(0, 0), (0, 1), (1, 1)]
    )


    # ---------------------------------------------------------
    # Test 9: Verify operation_summary remains deterministic
    # ---------------------------------------------------------
    cost = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]

    result = minimum_cost_grid_path(
        cost,
        operation_summary=True
    )

    assert result["minimum_cost"] == 21

    assert result["path"] == [
        (0, 0),
        (0, 1),
        (0, 2),
        (1, 2),
        (2, 2)
    ]

    # (rows - 1) * (cols - 1) = 2 * 2 = 4
    assert result["operation_summary"] == {
        "operation_count": 4
    }


    # ---------------------------------------------------------
    # Test 10: Original output is unchanged when the feature
    # is not requested.
    # ---------------------------------------------------------
    cost = [
        [1, 1],
        [1, 1]
    ]

    original_result = minimum_cost_grid_path(cost)

    assert isinstance(original_result, tuple)
    assert len(original_result) == 2
    assert original_result == (
        3,
        [(0, 0), (0, 1), (1, 1)]
    )


    print("All boundary and deterministic tie-handling tests passed.")


# =============================================================
# Run tests
# =============================================================

if __name__ == "__main__":
    run_tests()

    # Example normal usage
    cost = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]

    print("\nOriginal output:")
    print(minimum_cost_grid_path(cost))

    print("\nOutput with operation_summary:")
    print(
        minimum_cost_grid_path(
            cost,
            operation_summary=True
        )
    )