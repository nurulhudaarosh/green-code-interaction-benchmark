import sys

def solve_tsp(dist):
    """
    Traveling Salesperson Solver using Held-Karp subset dynamic programming.

    Problem:
        Given a complete symmetric distance matrix with at most 14 cities,
        find the minimum Hamiltonian cycle starting and ending at city 0.

    Tie handling:
        On ties, prefer the smaller predecessor.

        - During DP transitions to state (nmask, j): if two predecessors i1 < i2
          give the same cost, keep i1.
        - During the final cycle closure (edge i -> 0): if two last cities give
          the same total cost, prefer the smaller last city (which is the
          predecessor of city 0 in the cycle).

    Returns:
        (min_cost, tour) where tour starts and ends at 0.
    """
    n = len(dist)

    if n == 1:
        return 0, [0, 0]
    if n == 2:
        return 2 * dist[0][1], [0, 1, 0]

    FULL = 1 << n
    INF = float('inf')

    # dp[mask][i] = min cost to start at 0, visit exactly cities in mask, end at i
    dp = [[INF] * n for _ in range(FULL)]
    # parent[mask][i] = chosen predecessor of i for the optimal path to (mask, i)
    parent = [[-1] * n for _ in range(FULL)]

    # Base: start at city 0, only city 0 visited
    dp[1][0] = 0

    for mask in range(FULL):
        if not (mask & 1):
            continue  # every reachable state must include city 0
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
                    # Deterministic tie-break: prefer smaller predecessor i
                    if parent[nmask][j] == -1 or i < parent[nmask][j]:
                        parent[nmask][j] = i

    full = FULL - 1

    # Close the cycle: last city i -> city 0
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
            # Deterministic tie-break: predecessor of 0 is the last city i;
            # prefer the smaller one.
            if best_last == -1 or i < best_last:
                best_last = i

    # Reconstruct the tour backwards from best_last
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
    data = sys.stdin.read().split()
    if not data:
        return

    idx = 0
    n = int(data[idx]); idx += 1

    dist = []
    for _ in range(n):
        row = []
        for _ in range(n):
            row.append(int(data[idx])); idx += 1
        dist.append(row)

    cost, tour = solve_tsp(dist)

    print(f"Minimum cost: {cost}")
    print("Tour:", " -> ".join(map(str, tour)))


if __name__ == "__main__":
    main()