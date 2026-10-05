import sys
import json


def solve_tsp(dist, include_summary=False):
    """Held-Karp TSP from and to city 0.

    Default (include_summary=False): returns (min_cost, tour), unchanged.
    include_summary=True: returns (min_cost, tour, operation_summary).
    Ties are resolved in favor of the smaller predecessor.
    """
    n = len(dist)
    ops = {
        "base_initializations": 0,
        "transition_evaluations": 0,
        "transition_updates": 0,
        "closing_evaluations": 0,
        "closing_updates": 0,
        "reconstruction_steps": 0,
        "total_operations": 0,
    }

    def finish(cost, tour):
        if include_summary:
            ops["total_operations"] = (
                ops["base_initializations"]
                + ops["transition_evaluations"]
                + ops["closing_evaluations"]
                + ops["reconstruction_steps"]
            )
            return cost, tour, ops
        return cost, tour

    if n == 0:
        return finish(0, [])
    if n == 1:
        return finish(0, [0, 0])
    if n == 2:
        return finish(dist[0][1] + dist[1][0], [0, 1, 0])

    m = n - 1                      # cities 1..n-1 map to bits 0..m-1
    full = (1 << m) - 1
    INF = float("inf")

    dp = [[INF] * m for _ in range(1 << m)]
    parent = [[-1] * m for _ in range(1 << m)]

    for j in range(m):
        dp[1 << j][j] = dist[0][j + 1]
        ops["base_initializations"] += 1

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
                ops["transition_evaluations"] += 1
                cand = prev_row[i] + dist[i + 1][j + 1]
                if cand < best:
                    best = cand
                    best_i = i
                    ops["transition_updates"] += 1
            row[j] = best
            parent[mask][j] = best_i

    # Close the cycle; ascending j + strict '<' => smaller last city wins ties
    best_cost = INF
    last = -1
    for j in range(m):
        ops["closing_evaluations"] += 1
        cand = dp[full][j] + dist[j + 1][0]
        if cand < best_cost:
            best_cost = cand
            last = j
            ops["closing_updates"] += 1

    # Reconstruct
    path = []
    mask = full
    cur = last
    while cur != -1:
        ops["reconstruction_steps"] += 1
        path.append(cur + 1)
        prev = parent[mask][cur]
        mask ^= (1 << cur)
        cur = prev
    path.reverse()

    return finish(best_cost, [0] + path + [0])


def main():
    args = sys.argv[1:]
    want_summary = "--summary" in args

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

    if want_summary:
        cost, tour, summary = solve_tsp(dist, include_summary=True)
    else:
        cost, tour = solve_tsp(dist)

    print(cost)
    print(" ".join(map(str, tour)))
    if want_summary:
        print("operation_summary:", json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()