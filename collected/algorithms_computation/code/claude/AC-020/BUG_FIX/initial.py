import sys


def solve_tsp(dist):
    """Return (min_cost, tour) for the minimum Hamiltonian cycle from city 0.

    tour is a list starting and ending at city 0.
    Ties are resolved in favor of the smaller predecessor.
    """
    n = len(dist)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0, 0]

    m = n - 1                      # cities 1..n-1 map to bits 0..m-1
    full = (1 << m) - 1
    INF = float("inf")

    dp = [[INF] * m for _ in range(1 << m)]
    parent = [[-1] * m for _ in range(1 << m)]   # -1 means predecessor is city 0

    # Base cases: path 0 -> j
    for j in range(m):
        dp[1 << j][j] = dist[0][j + 1]

    # Masks in increasing order guarantee subsets are processed first
    for mask in range(1, full + 1):
        for j in range(m):
            if not (mask >> j) & 1:
                continue
            prev_mask = mask ^ (1 << j)
            if prev_mask == 0:
                continue           # base case already set
            best = INF
            best_i = -1
            for i in range(m):     # increasing i => smaller predecessor wins ties
                if not (prev_mask >> i) & 1:
                    continue
                cand = dp[prev_mask][i] + dist[i + 1][j + 1]
                if cand < best:    # strict: keeps the first (smallest) i on ties
                    best = cand
                    best_i = i
            dp[mask][j] = best
            parent[mask][j] = best_i

    # Close the cycle back to city 0
    best_cost = INF
    last = -1
    for j in range(m):             # increasing j => smaller predecessor of city 0 wins ties
        cand = dp[full][j] + dist[j + 1][0]
        if cand < best_cost:
            best_cost = cand
            last = j

    # Reconstruct the tour by walking parents backward
    path = []
    mask = full
    cur = last
    while cur != -1:
        path.append(cur + 1)
        prev = parent[mask][cur]
        mask ^= (1 << cur)
        cur = prev
    path.reverse()

    tour = [0] + path + [0]
    return best_cost, tour


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    vals = list(map(int, data[1:1 + n * n]))
    dist = [vals[i * n:(i + 1) * n] for i in range(n)]
    cost, tour = solve_tsp(dist)
    print(cost)
    print(" ".join(map(str, tour)))


if __name__ == "__main__":
    main()