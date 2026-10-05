from typing import List, Tuple, Optional, Dict, Any


def min_cost_path(
    cost: List[List[int]],
    return_operation_summary: bool = False,
) -> Tuple[int, List[Tuple[int, int]]] | Tuple[int, List[Tuple[int, int]], Dict[str, Any]]:
    """
    Minimum-cost path from top-left to bottom-right, moving only right or down.

    Tie rule (deterministic): when dp[i-1][j] == dp[i][j-1], prefer the
    predecessor (i-1, j), i.e. the move *into* (i, j) is a DOWN move.

    Returns:
        (min_cost, path)                                  by default
        (min_cost, path, operation_summary)               if return_operation_summary=True

    operation_summary keys:
        decisions      : interior cells where two predecessors were compared
        tie_decisions  : those comparisons that were ties
        forced_cells   : cells filled from a single predecessor (base + row0 + col0)
    """
    if not cost or not cost[0]:
        raise ValueError("Cost matrix must be non-empty")
    m, n = len(cost), len(cost[0])
    if any(len(row) != n for row in cost):
        raise ValueError("Cost matrix must be rectangular")
    if any(c < 0 for row in cost for c in row):
        raise ValueError("Costs must be non-negative")

    dp = [[0] * n for _ in range(m)]
    pred: List[List[Optional[Tuple[int, int]]]] = [[None] * n for _ in range(m)]

    decisions = 0
    tie_decisions = 0
    forced_cells = 0

    # Base cell: forced, no decision.
    dp[0][0] = cost[0][0]
    forced_cells += 1

    # First row: forced (only left predecessor).
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + cost[0][j]
        pred[0][j] = (0, j - 1)
        forced_cells += 1

    # First column: forced (only top predecessor).
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + cost[i][0]
        pred[i][0] = (i - 1, 0)
        forced_cells += 1

    # Interior cells: each is a major decision between two predecessors.
    for i in range(1, m):
        for j in range(1, n):
            from_top = dp[i - 1][j]
            from_left = dp[i][j - 1]
            decisions += 1
            if from_top <= from_left:          # tie -> prefer DOWN into (i, j)
                if from_top == from_left:
                    tie_decisions += 1
                dp[i][j] = from_top + cost[i][j]
                pred[i][j] = (i - 1, j)
            else:
                dp[i][j] = from_left + cost[i][j]
                pred[i][j] = (i, j - 1)

    # Reconstruct path.
    path: List[Tuple[int, int]] = []
    cur: Optional[Tuple[int, int]] = (m - 1, n - 1)
    while cur is not None:
        path.append(cur)
        cur = pred[cur[0]][cur[1]]
    path.reverse()

    if not return_operation_summary:
        return dp[m - 1][n - 1], path

    operation_summary: Dict[str, Any] = {
        "decisions": decisions,
        "tie_decisions": tie_decisions,
        "forced_cells": forced_cells,
    }
    return dp[m - 1][n - 1], path, operation_summary


if __name__ == "__main__":
    # Original behavior: exactly two values, unchanged.
    g = [[0, 1], [1, 0]]
    c, p = min_cost_path(g)
    assert c == 1 and p == [(0, 0), (0, 1), (1, 1)], (c, p)
    print("default (2-tuple):", c, p)

    # Feature requested: 3-tuple with operation_summary.
    c, p, s = min_cost_path(g, return_operation_summary=True)
    assert c == 1 and p == [(0, 0), (0, 1), (1, 1)], (c, p)
    assert s == {"decisions": 1, "tie_decisions": 1, "forced_cells": 3}, s
    print("with summary:    ", c, p, s)

    # Classic example.
    g2 = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
    c2, p2, s2 = min_cost_path(g2, return_operation_summary=True)
    assert c2 == 7, c2
    assert s2["decisions"] == (3 - 1) * (3 - 1) == 4, s2
    print("example:         ", c2, p2, s2)

    # Edge cases: original outputs preserved; summaries deterministic.
    assert min_cost_path([[42]]) == (42, [(0, 0)])
    assert min_cost_path([[42]], True)[2] == {
        "decisions": 0, "tie_decisions": 0, "forced_cells": 1,
    }
    assert min_cost_path([[1, 2, 3]]) == (6, [(0, 0), (0, 1), (0, 2)])
    assert min_cost_path([[1], [2], [3]]) == (6, [(0, 0), (1, 0), (2, 0)])
    print("edge cases OK")