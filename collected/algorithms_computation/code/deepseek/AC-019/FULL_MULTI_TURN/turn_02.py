from typing import List, Tuple, Optional


def min_cost_path(cost: List[List[int]]) -> Tuple[int, List[Tuple[int, int]]]:
    """
    Minimum-cost path from top-left to bottom-right, moving only right or down.

    Tie rule (deterministic): when dp[i-1][j] == dp[i][j-1], prefer the
    predecessor (i-1, j), i.e. the move *into* (i, j) is a DOWN move.
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

    dp[0][0] = cost[0][0]

    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + cost[0][j]
        pred[0][j] = (0, j - 1)

    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + cost[i][0]
        pred[i][0] = (i - 1, 0)

    for i in range(1, m):
        for j in range(1, n):
            from_top = dp[i - 1][j]
            from_left = dp[i][j - 1]
            if from_top <= from_left:          # tie -> prefer DOWN into (i, j)
                dp[i][j] = from_top + cost[i][j]
                pred[i][j] = (i - 1, j)
            else:
                dp[i][j] = from_left + cost[i][j]
                pred[i][j] = (i, j - 1)

    path: List[Tuple[int, int]] = []
    cur: Optional[Tuple[int, int]] = (m - 1, n - 1)
    while cur is not None:
        path.append(cur)
        cur = pred[cur[0]][cur[1]]
    path.reverse()
    return dp[m - 1][n - 1], path


if __name__ == "__main__":
    # Tie case: rule says prefer DOWN into the tie cell -> path via (0,1)
    g = [[0, 1], [1, 0]]
    c, p = min_cost_path(g)
    assert c == 1, c
    assert p == [(0, 0), (0, 1), (1, 1)], p
    print("tie case OK:", c, p)

    # Classic example
    g2 = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
    c2, p2 = min_cost_path(g2)
    assert c2 == 7, c2
    print("example OK:", c2, p2)

    # Single cell
    assert min_cost_path([[42]]) == (42, [(0, 0)])
    # Single row
    assert min_cost_path([[1, 2, 3]]) == (6, [(0, 0), (0, 1), (0, 2)])
    # Single column
    assert min_cost_path([[1], [2], [3]]) == (6, [(0, 0), (1, 0), (2, 0)])
    print("edge cases OK")