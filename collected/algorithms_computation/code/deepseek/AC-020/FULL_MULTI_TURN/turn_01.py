import sys

def solve_tsp(dist):
    """
    Solve TSP starting/ending at city 0 using Held-Karp DP.
    Returns (min_cost, tour) where tour is a list starting and ending at 0.
    Ties prefer the smaller predecessor.
    """
    n = len(dist)
    if n == 1:
        return 0, [0, 0]
    if n == 2:
        return dist[0][1] * 2, [0, 1, 0]

    full_mask = (1 << n) - 1
    INF = float('inf')

    # dp[mask][i] = min cost to start at 0, visit cities in mask, end at i
    # parent[mask][i] = predecessor j that achieved dp[mask][i]
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]

    dp[1][0] = 0  # only city 0 visited, currently at 0

    for mask in range(1 << n):
        if not (mask & 1):  # must include city 0
            continue
        for i in range(n):
            if not (mask & (1 << i)):
                continue
            if dp[mask][i] == INF:
                continue
            # Try extending to city k not in mask
            for k in range(n):
                if mask & (1 << k):
                    continue
                new_mask = mask | (1 << k)
                new_cost = dp[mask][i] + dist[i][k]
                if new_cost < dp[new_mask][k]:
                    dp[new_mask][k] = new_cost
                    parent[new_mask][k] = i
                elif new_cost == dp[new_mask][k] and new_cost != INF:
                    # Tie: prefer smaller predecessor
                    if parent[new_mask][k] == -1 or i < parent[new_mask][k]:
                        parent[new_mask][k] = i

    # Close the tour: return to city 0
    best_cost = INF
    best_last = -1
    for i in range(1, n):
        if dp[full_mask][i] == INF:
            continue
        total = dp[full_mask][i] + dist[i][0]
        if total < best_cost:
            best_cost = total
            best_last = i
        elif total == best_cost:
            # Tie: prefer smaller predecessor (i here is predecessor of 0)
            if best_last == -1 or i < best_last:
                best_last = i

    if best_last == -1:
        return None, None  # no tour (shouldn't happen for complete graph)

    # Reconstruct tour by walking parent pointers backward
    tour = []
    mask = full_mask
    cur = best_last
    while cur != -1:
        tour.append(cur)
        prev = parent[mask][cur]
        mask ^= (1 << cur)
        cur = prev

    tour.reverse()
    tour.append(0)  # close the cycle
    return best_cost, tour


def main():
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
    print(cost)
    print(' '.join(map(str, tour)))


if __name__ == "__main__":
    main()