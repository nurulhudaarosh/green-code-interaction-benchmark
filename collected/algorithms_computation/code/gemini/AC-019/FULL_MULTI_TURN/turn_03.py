"""
Minimum-Cost Grid Path Solver with Operation Summary Feature

Problem Restatement:
Given an m x n grid filled with non-negative costs, move only Right or Down 
from top-left (0, 0) to bottom-right (m-1, n-1). Find the minimum cumulative 
path cost and construct one deterministic optimal path using dynamic programming 
with predecessor tracking and deterministic tie handling.

Original Required Outputs:
- Minimum path cost (int)
- Deterministic optimal path (list of coordinate tuples)

Added Feature:
- Optional parameter `include_summary: bool = False`.
- When False (default): returns original 2-tuple `(cost, path)`.
- When True: returns 3-tuple `(cost, path, operation_summary)`, where 
  `operation_summary` is a dictionary containing deterministic statistics 
  of the computation (e.g., total cell evaluations, tie-break resolutions, 
  and total DP transitions).
"""


def min_path_cost(
    grid: list[list[int]], include_summary: bool = False
) -> tuple[int, list[tuple[int, int]]] | tuple[
    int, list[tuple[int, int]], dict[str, int]
]:
    """Finds minimum path cost, a deterministic path, and an optional operation summary."""
    if not grid or not grid[0]:
        summary = {
            "cell_evaluations": 0,
            "boundary_initializations": 0,
            "dp_transitions": 0,
            "ties_encountered": 0,
            "backtrack_steps": 0,
        }
        return (0, [], summary) if include_summary else (0, [])

    m, n = len(grid), len(grid[0])

    dp = [[0] * n for _ in range(m)]
    parent = [[None] * n for _ in range(m)]

    # Tracking operation metrics
    boundary_inits = 1  # Starting cell (0, 0)
    dp_transitions = 0
    ties_encountered = 0

    dp[0][0] = grid[0][0]

    # Initialize top row
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + grid[0][j]
        parent[0][j] = (0, j - 1)
        boundary_inits += 1

    # Initialize left column
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + grid[i][0]
        parent[i][0] = (i - 1, 0)
        boundary_inits += 1

    # Fill DP table with explicit deterministic tie handling
    for i in range(1, m):
        for j in range(1, n):
            dp_transitions += 1
            from_up = dp[i - 1][j]
            from_left = dp[i][j - 1]

            if from_left == from_up:
                ties_encountered += 1

            # Prioritize LEFT over UP on equality
            if from_left <= from_up:
                dp[i][j] = grid[i][j] + from_left
                parent[i][j] = (i, j - 1)
            else:
                dp[i][j] = grid[i][j] + from_up
                parent[i][j] = (i - 1, j)

    # Reconstruct optimal path from parent matrix
    path = []
    curr = (m - 1, n - 1)
    backtrack_steps = 0

    while curr is not None:
        path.append(curr)
        curr = parent[curr[0]][curr[1]]
        backtrack_steps += 1

    path.reverse()

    min_cost = dp[m - 1][n - 1]

    if include_summary:
        operation_summary = {
            "total_cells": m * n,
            "boundary_initializations": boundary_inits,
            "dp_transitions": dp_transitions,
            "ties_encountered": ties_encountered,
            "backtrack_steps": backtrack_steps,
            "total_major_operations": boundary_inits
            + dp_transitions
            + backtrack_steps,
        }
        return min_cost, path, operation_summary

    return min_cost, path


if __name__ == "__main__":
    grid = [[1, 2], [2, 1]]

    # 1. Original behavior (Backward compatible, 2-tuple output)
    cost, path = min_path_cost(grid)
    print("Default Output:")
    print("Cost:", cost)
    print("Path:", path)

    print("\n" + "-" * 40 + "\n")

    # 2. Enhanced behavior with operation summary (3-tuple output)
    cost, path, summary = min_path_cost(grid, include_summary=True)
    print("With Operation Summary:")
    print("Cost:", cost)
    print("Path:", path)
    print("Operation Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")