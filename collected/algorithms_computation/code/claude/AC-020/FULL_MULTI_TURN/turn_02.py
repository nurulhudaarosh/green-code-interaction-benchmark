from itertools import permutations
from typing import List, Tuple

INF = float("inf")


def held_karp(dist: List[List[float]]) -> Tuple[float, List[int]]:
    """Minimum Hamiltonian cycle from/to city 0 via Held-Karp.

    Tie rule: at every step the smaller predecessor wins. That covers the
    DP transitions and the closing edge back to city 0, where the
    predecessor of city 0 is the last city visited.
    """
    n = len(dist)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0, 0]

    m = n - 1                                   # cities 1..n-1 -> bits 0..m-1
    full = (1 << m) - 1
    dp = [[INF] * m for _ in range(1 << m)]
    parent = [[-1] * m for _ in range(1 << m)]  # -1 => predecessor is city 0

    for j in range(m):
        dp[1 << j][j] = dist[0][j + 1]

    for mask in range(1, 1 << m):
        for j in range(m):
            if not (mask >> j) & 1:
                continue
            prev = mask ^ (1 << j)
            if prev == 0:
                continue
            best, best_i = INF, -1
            for i in range(m):                  # ascending, strict '<'
                if (prev >> i) & 1:
                    cand = dp[prev][i] + dist[i + 1][j + 1]
                    if cand < best:
                        best, best_i = cand, i
            dp[mask][j] = best
            parent[mask][j] = best_i

    best_cost, last = INF, -1
    for j in range(m):                          # smaller last city wins ties
        cand = dp[full][j] + dist[j + 1][0]
        if cand < best_cost:
            best_cost, last = cand, j

    path, mask, j = [], full, last
    while j != -1:
        path.append(j + 1)
        p = parent[mask][j]
        mask ^= 1 << j
        j = p
    path.reverse()
    return best_cost, [0] + path + [0]


def brute_force(dist: List[List[float]]) -> Tuple[float, List[int]]:
    """Reference: min cost, ties broken by the tour read backwards
    (last city first) being lexicographically smallest."""
    n = len(dist)
    best = None
    for p in permutations(range(1, n)):
        t = [0, *p, 0]
        c = sum(dist[a][b] for a, b in zip(t, t[1:]))
        key = (c, t[::-1])
        if best is None or key < best:
            best = key
    return best[0], best[1][::-1]


if __name__ == "__main__":
    sample = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]
    cost, tour = held_karp(sample)
    print("Minimum cost:", cost)          # 80
    print("Tour:", tour)                  # [0, 2, 3, 1, 0]
    assert (cost, tour) == (80, [0, 2, 3, 1, 0])

    # Tie-heavy checks against the brute-force reference.
    for n in range(2, 8):
        equal = [[0 if i == j else 1 for j in range(n)] for i in range(n)]
        assert held_karp(equal) == brute_force(equal), n
        # Deterministic pseudo-varied matrix with many ties (no randomness).
        mix = [[0 if i == j else 1 + (i + j) % 3 for j in range(n)] for i in range(n)]
        assert held_karp(mix) == brute_force(mix), n
    print("All checks passed.")