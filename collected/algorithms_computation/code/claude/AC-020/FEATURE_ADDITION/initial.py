import sys
import json


def solve_tsp(dist):
    """Return (min_cost, tour) where tour starts and ends at city 0.

    Ties are resolved in favor of the smaller predecessor.
    """
    n = len(dist)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0, 0]
    if n == 2:
        return dist[0][1] + dist[1][0], [0, 1, 0]

    m = n - 1                      # cities 1..n-1 map to bits 0..m-1
    full = (1 << m) - 1
    INF = float("inf")

    dp = [[INF] * m for _ in range(1 << m)]
    parent = [[-1] * m for _ in range(1 << m)]

    for j in range(m):
        dp[1 << j][j] = dist[0][j + 1]

    for mask in range(1, 1 << m):
        row = dp[mask]
        for j in range(m):
            if not (mask >> j) & 1:
                continue
            prev_mask = mask ^ (1 << j)
            if prev_mask == 0:
                continue           # base case already set
            prev_row = dp[prev_mask]
            best = INF
            best_i = -1
            # ascending i + strict '<' => smaller predecessor wins ties
            for i in range(m):
                if not (prev_mask >> i) & 1:
                    continue
                cand = prev_row[i] + dist[i + 1][j + 1]
                if cand < best:
                    best = cand
                    best_i = i
            row[j] = best
            parent[mask][j] = best_i

    # Close the cycle; ascending j + strict '<' => smaller last city wins ties
    best_cost = INF
    last = -1
    for j in range(m):
        cand = dp[full][j] + dist[j + 1][0]
        if cand < best_cost:
            best_cost = cand
            last = j

    # Reconstruct
    path = []
    mask = full
    cur = last
    while cur != -1:
        path.append(cur + 1)
        prev = parent[mask][cur]
        mask ^= (1 << cur)
        cur = prev
    path.reverse()

    return best_cost, [0] + path + [0]


def main():
    data = sys.stdin.read().strip()
    if not data:
        return
    try:
        dist = json.loads(data)          # JSON matrix, e.g. [[0,1],[1,0]]
    except json.JSONDecodeError:
        tokens = data.split()            # or: n followed by n*n numbers
        n = int(tokens[0])
        vals = [float(x) if "." in x else int(x) for x in tokens[1:1 + n * n]]
        dist = [vals[r * n:(r + 1) * n] for r in range(n)]

    cost, tour = solve_tsp(dist)
    print(cost)
    print(" ".join(map(str, tour)))


if __name__ == "__main__":
    main()