from typing import List, Tuple

INF = float("inf")


def held_karp(dist: List[List[float]]) -> Tuple[float, List[int]]:
    """Return (min_cost, tour) for the shortest Hamiltonian cycle from city 0.

    Ties are broken in favor of the smaller predecessor city.
    """
    n = len(dist)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0, 0]

    m = n - 1                      # cities 1..n-1 map to bits 0..m-1
    full = (1 << m) - 1
    dp = [[INF] * m for _ in range(1 << m)]
    parent = [[-1] * m for _ in range(1 << m)]   # -1 means predecessor is city 0

    for j in range(m):
        dp[1 << j][j] = dist[0][j + 1]

    for mask in range(1, 1 << m):
        for j in range(m):
            if not (mask >> j) & 1:
                continue
            prev = mask ^ (1 << j)
            if prev == 0:
                continue           # base case already set
            best, best_i = INF, -1
            for i in range(m):     # ascending i -> smaller predecessor wins ties
                if (prev >> i) & 1:
                    cand = dp[prev][i] + dist[i + 1][j + 1]
                    if cand < best:
                        best, best_i = cand, i
            dp[mask][j] = best
            parent[mask][j] = best_i

    # Close the cycle back to city 0; smaller last city wins ties.
    best_cost, last = INF, -1
    for j in range(m):
        cand = dp[full][j] + dist[j + 1][0]
        if cand < best_cost:
            best_cost, last = cand, j

    # Reconstruct the path.
    path = []
    mask, j = full, last
    while j != -1:
        path.append(j + 1)
        p = parent[mask][j]
        mask ^= 1 << j
        j = p
    path.reverse()

    return best_cost, [0] + path + [0]


if __name__ == "__main__":
    # Fixed deterministic example (4 cities).
    matrix = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]
    cost, tour = held_karp(matrix)
    print("Minimum cost:", cost)
    print("Tour:", tour)