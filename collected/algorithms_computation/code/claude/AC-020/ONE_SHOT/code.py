from typing import List, Tuple

INF = float("inf")


def tsp_held_karp(dist: List[List[float]]) -> Tuple[float, List[int]]:
    """
    Minimum Hamiltonian cycle starting and ending at city 0.
    Returns (min_cost, tour) where tour = [0, ..., 0].
    Ties are broken in favor of the smaller predecessor.
    """
    n = len(dist)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0, 0]
    if n == 2:
        return dist[0][1] + dist[1][0], [0, 1, 0]

    m = n - 1                      # cities 1..n-1 map to bits 0..m-1
    size = 1 << m
    dp = [[INF] * n for _ in range(size)]
    parent = [[-1] * n for _ in range(size)]

    # Base cases: path 0 -> j
    for j in range(1, n):
        mask = 1 << (j - 1)
        dp[mask][j] = dist[0][j]
        parent[mask][j] = 0

    # Fill DP in increasing mask order (subsets are always smaller numbers)
    for mask in range(1, size):
        for j in range(1, n):
            bit_j = 1 << (j - 1)
            if not (mask & bit_j):
                continue
            prev_mask = mask ^ bit_j
            if prev_mask == 0:
                continue  # base case already set
            best = INF
            best_k = -1
            for k in range(1, n):          # ascending -> smaller predecessor wins ties
                if not (prev_mask & (1 << (k - 1))):
                    continue
                cand = dp[prev_mask][k] + dist[k][j]
                if cand < best:            # strict: keep the first (smallest) k on ties
                    best = cand
                    best_k = k
            dp[mask][j] = best
            parent[mask][j] = best_k

    # Close the cycle back to city 0
    full = size - 1
    best_cost = INF
    last = -1
    for j in range(1, n):                  # ascending, strict -> smaller last city on ties
        cand = dp[full][j] + dist[j][0]
        if cand < best_cost:
            best_cost = cand
            last = j

    # Reconstruct the tour
    path = []
    mask = full
    cur = last
    while cur != 0:
        path.append(cur)
        prev = parent[mask][cur]
        mask ^= 1 << (cur - 1)
        cur = prev
    path.reverse()
    tour = [0] + path + [0]
    return best_cost, tour


if __name__ == "__main__":
    example = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]
    cost, tour = tsp_held_karp(example)
    print(cost)   # 80
    print(tour)   # [0, 1, 3, 2, 0]