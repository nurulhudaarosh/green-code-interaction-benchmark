def solve_tsp(dist):
    """
    Solve TSP using Held-Karp DP.
    dist: n x n symmetric distance matrix, start/end at city 0.
    Returns (min_cost, tour) where tour starts and ends at 0.
    Ties prefer smaller predecessor.
    """
    n = len(dist)
    if n == 1:
        return 0, [0, 0]
    if n == 2:
        return dist[0][1] * 2, [0, 1, 0]

    FULL = 1 << n
    INF = float('inf')

    # dp[mask][i] = min cost to start at 0, visit mask, end at i
    dp = [[INF] * n for _ in range(FULL)]
    parent = [[-1] * n for _ in range(FULL)]

    dp[1][0] = 0  # start at city 0, mask = {0}

    for mask in range(FULL):
        if not (mask & 1):
            continue  # must include city 0
        for i in range(n):
            if dp[mask][i] == INF:
                continue
            if not (mask & (1 << i)):
                continue
            for j in range(n):
                if mask & (1 << j):
                    continue
                nmask = mask | (1 << j)
                ncost = dp[mask][i] + dist[i][j]
                if ncost < dp[nmask][j]:
                    dp[nmask][j] = ncost
                    parent[nmask][j] = i
                elif ncost == dp[nmask][j]:
                    # Tie: prefer smaller predecessor
                    if parent[nmask][j] == -1 or i < parent[nmask][j]:
                        parent[nmask][j] = i

    full = FULL - 1
    best_cost = INF
    best_last = -1
    for i in range(1, n):
        if dp[full][i] == INF:
            continue
        total = dp[full][i] + dist[i][0]
        if total < best_cost:
            best_cost = total
            best_last = i
        elif total == best_cost:
            # Tie: prefer smaller predecessor (smaller i)
            if best_last == -1 or i < best_last:
                best_last = i

    # Reconstruct tour
    tour = []
    mask = full
    cur = best_last
    while cur != -1:
        tour.append(cur)
        p = parent[mask][cur]
        mask ^= (1 << cur)
        cur = p
    tour.reverse()
    tour.append(0)

    return best_cost, tour


def main():
    import sys
    data = sys.stdin.read().split()
    if not data:
        return
    idx = 0
    n = int(data[idx]); idx += 1
    dist = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(int(data[idx])); idx += 1
        dist.append(row)

    cost, tour = solve_tsp(dist)
    print(f"Minimum cost: {cost}")
    print("Tour:", " -> ".join(map(str, tour)))


if __name__ == "__main__":
    main()