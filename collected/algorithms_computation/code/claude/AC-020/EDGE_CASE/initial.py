import sys
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Problem: complete symmetric distance matrix, n <= 14 cities.
# Find the minimum Hamiltonian cycle starting and ending at city 0.
# Ties prefer the smaller predecessor.
# Output: minimum cost and the tour, e.g. [0, 1, 3, 2, 0].
#
# Algorithm: Held-Karp subset DP.
#   dp[mask][j] = min cost of a path from 0 visiting exactly the cities in
#   `mask` (bit j-1 <-> city j) and ending at city j.
#   Base: dp[{j}][j] = dist[0][j]
#   Transition: dp[mask][j] = min_i dp[mask\{j}][i] + dist[i][j]
#   Answer: min_j dp[full][j] + dist[j][0]
#   Iterating i (and j) in ascending order with a strict "<" keeps the
#   smallest predecessor on ties.
# Complexity: O(2^(n-1) * n^2) time, O(2^(n-1) * n) memory.
# ---------------------------------------------------------------------------


def held_karp(dist: List[List[float]]) -> Tuple[float, List[int]]:
    n = len(dist)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0, 0]
    if n == 2:
        return dist[0][1] + dist[1][0], [0, 1, 0]

    m = n - 1
    full = (1 << m) - 1
    INF = float("inf")

    dp = [[INF] * n for _ in range(1 << m)]
    parent = [[-1] * n for _ in range(1 << m)]

    for j in range(1, n):
        dp[1 << (j - 1)][j] = dist[0][j]
        parent[1 << (j - 1)][j] = 0

    for mask in range(1, full + 1):
        row = dp[mask]
        for j in range(1, n):
            bit_j = 1 << (j - 1)
            if not (mask & bit_j):
                continue
            prev_mask = mask ^ bit_j
            if prev_mask == 0:
                continue
            prev_row = dp[prev_mask]
            best, best_i = INF, -1
            for i in range(1, n):
                if not (prev_mask & (1 << (i - 1))):
                    continue
                cand = prev_row[i] + dist[i][j]
                if cand < best:
                    best, best_i = cand, i
            row[j] = best
            parent[mask][j] = best_i

    best_cost, last = INF, -1
    for j in range(1, n):
        cand = dp[full][j] + dist[j][0]
        if cand < best_cost:
            best_cost, last = cand, j

    path = []
    mask, cur = full, last
    while cur != 0:
        path.append(cur)
        prev = parent[mask][cur]
        mask ^= 1 << (cur - 1)
        cur = prev
    path.reverse()

    return best_cost, [0] + path + [0]


def main() -> None:
    # Input (stdin): n, followed by n*n distances.
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    vals = [float(x) if ("." in x or "e" in x.lower()) else int(x)
            for x in data[1:1 + n * n]]
    dist = [vals[i * n:(i + 1) * n] for i in range(n)]
    cost, tour = held_karp(dist)
    print(cost)
    print(" ".join(map(str, tour)))


if __name__ == "__main__":
    main()