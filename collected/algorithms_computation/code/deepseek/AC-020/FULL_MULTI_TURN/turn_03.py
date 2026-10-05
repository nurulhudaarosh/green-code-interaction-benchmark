import os
import sys


def solve_tsp(dist, return_summary=False):
    """
    Exact TSP from city 0 using Held-Karp subset DP.

    Deterministic tie-breaking: on a cost tie, prefer the tour with the
    smaller predecessor at the latest differing position (equivalently,
    the lexicographically smaller reversed path).

    Returns:
        (cost, tour)                       if return_summary is False
        (cost, tour, operation_summary)    if return_summary is True

    operation_summary is a string:
        "dp_writes=<int>;closure_comparisons=<int>;total=<int>"
    where:
        dp_writes          = number of dp[mask][i] assignments (base case,
                             strict improvements, and tie-break replacements)
        closure_comparisons= number of final closure candidates examined
        total              = dp_writes + closure_comparisons
    """
    dp_writes = 0
    closure_comparisons = 0

    n = len(dist)

    def summary():
        return "dp_writes={};closure_comparisons={};total={}".format(
            dp_writes, closure_comparisons, dp_writes + closure_comparisons
        )

    if n == 1:
        # base case assignment still counted as one write
        dp_writes += 1
        result = (0, [0, 0])
        return result + (summary(),) if return_summary else result

    if n == 2:
        dp_writes += 1  # base case
        result = (dist[0][1] * 2, [0, 1, 0])
        return result + (summary(),) if return_summary else result

    size = 1 << n

    # dp[mask][i] = (cost, path_tuple) where path_tuple is the sequence
    # of cities from 0 up to and including i, visiting exactly the
    # cities in mask.
    dp = [[None] * n for _ in range(size)]
    dp[1][0] = (0, (0,))
    dp_writes += 1  # base case write

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
                    dp_writes += 1
                elif new_cost < cur[0]:
                    dp[new_mask][k] = (new_cost, new_path)
                    dp_writes += 1
                elif new_cost == cur[0]:
                    # Tie: prefer smaller predecessor at the latest
                    # differing position -> compare reversed paths.
                    if new_path[::-1] < cur[1][::-1]:
                        dp[new_mask][k] = (new_cost, new_path)
                        dp_writes += 1

    full_mask = size - 1
    best = None  # (total_cost, reversed_key, last_city, path)
    for i in range(1, n):
        state = dp[full_mask][i]
        if state is None:
            continue
        closure_comparisons += 1  # a closure candidate is examined
        cost_i, path_i = state
        total = cost_i + dist[i][0]
        key = (i,) + path_i[-2::-1]
        if best is None or total < best[0]:
            best = (total, key, i, path_i)
        elif total == best[0] and key < best[1]:
            best = (total, key, i, path_i)

    if best is None:
        result = (None, None)
        return result + (summary(),) if return_summary else result

    total, _, _, path = best
    tour = list(path) + [0]
    result = (total, tour)
    return result + (summary(),) if return_summary else result


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

    want_summary = ("--summary" in sys.argv[1:]) or (os.environ.get("TSP_SUMMARY") == "1")

    if want_summary:
        cost, tour, operation_summary = solve_tsp(dist, return_summary=True)
        print(cost)
        print(' '.join(map(str, tour)))
        print(operation_summary)
    else:
        cost, tour = solve_tsp(dist, return_summary=False)
        print(cost)
        print(' '.join(map(str, tour)))


if __name__ == "__main__":
    main()