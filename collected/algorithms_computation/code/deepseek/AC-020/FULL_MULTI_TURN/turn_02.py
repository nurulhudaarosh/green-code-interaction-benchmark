import sys


def solve_tsp(dist):
    """
    Exact TSP from city 0, Held-Karp subset DP.
    Deterministic tie-breaking: on a cost tie, prefer the tour with the
    smaller predecessor at the latest differing position (equivalently,
    the lexicographically smaller reversed path).
    Returns (min_cost, tour) with tour starting and ending at 0.
    """
    n = len(dist)
    if n == 1:
        return 0, [0, 0]
    if n == 2:
        return dist[0][1] * 2, [0, 1, 0]

    size = 1 << n

    # dp[mask][i] = (cost, path_tuple) where path_tuple is the sequence
    # of cities from 0 up to and including i, visiting exactly the
    # cities in mask. Tuple comparison gives deterministic tie-breaking.
    dp = [[None] * n for _ in range(size)]
    dp[1][0] = (0, (0,))

    for mask in range(size):
        if not (mask & 1):
            continue
        for i in range(n):
            if not (mask & (1 << i)):
                continue
            state = dp[mask][i]
            if state is None:
                continue
            cost_i, path_i = state
            for k in range(n):
                if mask & (1 << k):
                    continue
                new_mask = mask | (1 << k)
                new_cost = cost_i + dist[i][k]
                new_path = path_i + (k,)
                cur = dp[new_mask][k]
                if cur is None:
                    dp[new_mask][k] = (new_cost, new_path)
                elif new_cost < cur[0]:
                    dp[new_mask][k] = (new_cost, new_path)
                elif new_cost == cur[0]:
                    # Tie: prefer smaller predecessor at the latest
                    # differing position -> compare reversed paths.
                    if new_path[::-1] < cur[1][::-1]:
                        dp[new_mask][k] = (new_cost, new_path)

    full_mask = size - 1
    best = None  # (total_cost, reversed_key, last_city, path)
    for i in range(1, n):
        state = dp[full_mask][i]
        if state is None:
            continue
        cost_i, path_i = state
        total = cost_i + dist[i][0]
        # Reversed key: predecessor of 0 is i, then path_i[-2], ...
        key = (i,) + path_i[-2::-1]
        if best is None or total < best[0]:
            best = (total, key, i, path_i)
        elif total == best[0] and key < best[1]:
            best = (total, key, i, path_i)

    if best is None:
        return None, None

    total, _, _, path = best
    tour = list(path) + [0]
    return total, tour


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
    print(cost)
    print(' '.join(map(str, tour)))


if __name__ == "__main__":
    main()