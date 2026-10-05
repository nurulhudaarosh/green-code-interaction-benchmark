"""
Minimum-Cost Grid Path

Original problem:
Given a non-negative rectangular cost matrix, move only right or down
from the top-left cell (0, 0) to the bottom-right cell.

Original required outputs:
1. The minimum total path cost.
2. One deterministic optimal path as a list of (row, column) coordinates.

Existing requirements:
- Use dynamic programming.
- Store predecessor coordinates for path reconstruction.
- Move only right or down.
- Use deterministic tie handling.
- When the top and left predecessors have equal cost, choose the top
  predecessor.
- Use only the Python standard library.
- No randomness, network access, APIs, external services, or human
  interaction.

New feature:
If operation_summary is requested, return an additional
"operation_summary" field containing a deterministic summary of the
computation.

For this task, the summary reports the number of major computational
decisions/operations made by the algorithm.

Definition of operation_count:
- Each DP cell for which both a top and left predecessor exist counts
  as one major computational decision.
- Boundary-cell initialization is not counted as a major decision.
- Path reconstruction is not counted as a DP decision.
- Therefore, for an m x n grid, operation_count is:
      max(0, m - 1) * max(0, n - 1)

Output when operation_summary is disabled/not requested:
    (minimum_cost, path)

Output when operation_summary=True:
    {
        "minimum_cost": minimum_cost,
        "path": path,
        "operation_summary": {
            "operation_count": number_of_major_operations
        }
    }

This preserves the original output when the feature is not requested.
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
    Find the minimum-cost path from the top-left to the bottom-right.

    Parameters:
        cost:
            Non-negative rectangular cost matrix.

        operation_summary:
            If False, return the original output:
                (minimum_cost, path)

            If True, return:
                {
                    "minimum_cost": minimum_cost,
                    "path": path,
                    "operation_summary": {
                        "operation_count": ...
                    }
                }

    Tie-breaking:
        If top and left predecessors have equal cost,
        choose the top predecessor.
    """

    # -------------------------
    # Validate input
    # -------------------------
    if not cost:
        raise ValueError("Cost matrix must not be empty.")

    if not cost[0]:
        raise ValueError("Cost matrix must not contain an empty row.")

    cols = len(cost[0])

    if any(len(row) != cols for row in cost):
        raise ValueError("Cost matrix must be rectangular.")

    if any(value < 0 for row in cost for value in row):
        raise ValueError("All costs must be non-negative.")

    rows = len(cost)

    # -------------------------
    # DP tables
    # -------------------------
    # dp[r][c] = minimum cost to reach (r, c)
    dp = [[0] * cols for _ in range(rows)]

    # parent[r][c] = predecessor coordinate
    parent = [[None] * cols for _ in range(rows)]

    # -------------------------
    # Starting cell
    # -------------------------
    dp[0][0] = cost[0][0]

    # -------------------------
    # Boundary initialization
    # -------------------------
    # First column: only possible predecessor is above.
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + cost[r][0]
        parent[r][0] = (r - 1, 0)

    # First row: only possible predecessor is to the left.
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + cost[0][c]
        parent[0][c] = (0, c - 1)

    # -------------------------
    # Main DP computation
    # -------------------------
    operation_count = 0

    for r in range(1, rows):
        for c in range(1, cols):
            from_top = dp[r - 1][c]
            from_left = dp[r][c - 1]

            # This cell requires a major predecessor decision.
            operation_count += 1

            # Deterministic tie handling:
            # <= ensures that a tie always selects the top predecessor.
            if from_top <= from_left:
                dp[r][c] = from_top + cost[r][c]
                parent[r][c] = (r - 1, c)
            else:
                dp[r][c] = from_left + cost[r][c]
                parent[r][c] = (r, c - 1)

    # -------------------------
    # Reconstruct optimal path
    # -------------------------
    path = []

    r, c = rows - 1, cols - 1

    while True:
        path.append((r, c))

        if (r, c) == (0, 0):
            break

        r, c = parent[r][c]

    path.reverse()

    minimum_cost = dp[rows - 1][cols - 1]

    # -------------------------
    # Preserve original output
    # -------------------------
    if not operation_summary:
        return minimum_cost, path

    # -------------------------
    # New optional output
    # -------------------------
    return {
        "minimum_cost": minimum_cost,
        "path": path,
        "operation_summary": {
            "operation_count": operation_count
        }
    }


# =========================================================
# Examples / Tests
# =========================================================

if __name__ == "__main__":

    cost = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]

    # Original behavior is unchanged when the feature
    # is not requested.
    result = minimum_cost_grid_path(cost)

    print("Original output:")
    print(result)

    # Expected:
    # (
    #     7,
    #     [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
    # )


    # New behavior when operation_summary is requested.
    result_with_summary = minimum_cost_grid_path(
        cost,
        operation_summary=True
    )

    print("\nOutput with operation_summary:")
    print(result_with_summary)

    # For a 3 x 3 grid:
    # (3 - 1) * (3 - 1) = 4 major DP decisions.
    #
    # Expected:
    # {
    #     "minimum_cost": 7,
    #     "path": [
    #         (0, 0),
    #         (1, 0),
    #         (2, 0),
    #         (2, 1),
    #         (2, 2)
    #     ],
    #     "operation_summary": {
    #         "operation_count": 4
    #     }
    # }


    # Deterministic tie-breaking test.
    tie_cost = [
        [1, 1],
        [1, 1]
    ]

    tie_result = minimum_cost_grid_path(
        tie_cost,
        operation_summary=True
    )

    print("\nTie-breaking test:")
    print(tie_result)

    # Expected:
    # {
    #     "minimum_cost": 3,
    #     "path": [(0, 0), (0, 1), (1, 1)],
    #     "operation_summary": {
    #         "operation_count": 1
    #     }
    # }