import sys


def solve_tsp(dist):
    """Return (min_cost, tour) for the minimum Hamiltonian cycle from city 0.

    tour starts and ends at city 0. Ties prefer the smaller predecessor,
    both inside the DP and for the last city before returning to 0.
    """
    n = len(dist)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0, 0]

    m = n - 1                                   # cities 1..n-1 -> bits 0..m-1
    full = (1 << m) - 1
    INF = float("inf")

    dp = [[INF] * m for _ in range(1 << m)]
    parent = [[-1] * m for _ in range(1 << m)]  # -1 => predecessor is city 0

    for j in range(m):
        dp[1 << j][j] = dist[0][j + 1]

    for mask in range(1, full + 1):
        for j in range(m):
            if not (mask >> j) & 1:
                continue
            prev_mask = mask ^ (1 << j)
            if prev_mask == 0:
                continue
            best, best_i = INF, -1
            for i in range(m):                  # increasing i
                if (prev_mask >> i) & 1:
                    cand = dp[prev_mask][i] + dist[i + 1][j + 1]
                    if cand < best:             # strict: smaller i wins ties
                        best, best_i = cand, i
            dp[mask][j] = best
            parent[mask][j] = best_i

    best_cost, last = INF, -1
    for j in range(m):                          # increasing j
        cand = dp[full][j] + dist[j + 1][0]
        if cand < best_cost:                    # strict: smaller j wins ties
            best_cost, last = cand, j

    path, mask, cur = [], full, last
    while cur != -1:
        path.append(cur + 1)
        prev = parent[mask][cur]
        mask ^= 1 << cur
        cur = prev
    path.reverse()
    return best_cost, [0] + path + [0]


def _num(tok):
    try:
        return int(tok)
    except ValueError:
        return float(tok)


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    if len(data) < 1 + n * n:
        raise ValueError("expected %d matrix entries, got %d" % (n * n, len(data) - 1))
    vals = [_num(t) for t in data[1:1 + n * n]]
    dist = [vals[i * n:(i + 1) * n] for i in range(n)]
    cost, tour = solve_tsp(dist)
    print(cost)
    print(" ".join(map(str, tour)))


if __name__ == "__main__":
    main()