def solve_tsp(distance_matrix, return_operation_summary=False):
    """
    Solve TSP using Held-Karp subset DP.

    Returns:
        If return_operation_summary is False (default):
            (min_cost, optimal_path)
        If return_operation_summary is True:
            (min_cost, optimal_path, operation_summary)

    Ties prefer the smaller predecessor.
    """
    n = len(distance_matrix)

    # Counters for operation summary
    state_expansions = 0
    relaxation_attempts = 0
    dp_updates = 0
    tie_break_updates = 0
    final_selection_comparisons = 0
    reconstruction_steps = 0

    def _result(cost, path, summary):
        if return_operation_summary:
            return cost, path, summary
        return cost, path

    # Edge case: single city
    if n == 1:
        summary = {
            "state_expansions": 0,
            "relaxation_attempts": 0,
            "dp_updates": 0,
            "tie_break_updates": 0,
            "final_selection_comparisons": 0,
            "reconstruction_steps": 0,
            "total_major_operations": 0,
        }
        return _result(0, [0, 0], summary)

    # Edge case: two cities
    if n == 2:
        summary = {
            "state_expansions": 0,
            "relaxation_attempts": 0,
            "dp_updates": 0,
            "tie_break_updates": 0,
            "final_selection_comparisons": 0,
            "reconstruction_steps": 0,
            "total_major_operations": 0,
        }
        return _result(distance_matrix[0][1] * 2, [0, 1, 0], summary)

    INF = float('inf')
    FULL_MASK = (1 << n) - 1

    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]

    dp[1][0] = 0

    for mask in range(1, 1 << n):
        if not (mask & 1):
            continue
        for i in range(n):
            if not (mask & (1 << i)):
                continue
            if dp[mask][i] == INF:
                continue

            state_expansions += 1

            for j in range(n):
                if mask & (1 << j):
                    continue
                relaxation_attempts += 1
                new_mask = mask | (1 << j)
                new_cost = dp[mask][i] + distance_matrix[i][j]
                if new_cost < dp[new_mask][j]:
                    dp[new_mask][j] = new_cost
                    parent[new_mask][j] = i
                    dp_updates += 1
                elif new_cost == dp[new_mask][j]:
                    if parent[new_mask][j] == -1 or i < parent[new_mask][j]:
                        parent[new_mask][j] = i
                    tie_break_updates += 1

    # Final selection: close the cycle back to city 0
    best_cost = INF
    best_last = -1
    for i in range(1, n):
        if dp[FULL_MASK][i] == INF:
            continue
        final_selection_comparisons += 1
        total = dp[FULL_MASK][i] + distance_matrix[i][0]
        if total < best_cost:
            best_cost = total
            best_last = i
        elif total == best_cost:
            if i < best_last:
                best_last = i

    # Reconstruct path
    path = []
    mask = FULL_MASK
    current = best_last
    while current != -1:
        reconstruction_steps += 1
        path.append(current)
        prev = parent[mask][current]
        mask ^= (1 << current)
        current = prev

    path.reverse()
    path.append(0)

    summary = {
        "state_expansions": state_expansions,
        "relaxation_attempts": relaxation_attempts,
        "dp_updates": dp_updates,
        "tie_break_updates": tie_break_updates,
        "final_selection_comparisons": final_selection_comparisons,
        "reconstruction_steps": reconstruction_steps,
        "total_major_operations": (
            state_expansions
            + relaxation_attempts
            + dp_updates
            + tie_break_updates
            + final_selection_comparisons
            + reconstruction_steps
        ),
    }

    return _result(best_cost, path, summary)


def main():
    import sys
    import json

    data = sys.stdin.read().strip().split()
    if not data:
        return

    idx = 0
    n = int(data[idx]); idx += 1

    dist = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(int(data[idx]))
            idx += 1
        dist.append(row)

    cost, path, summary = solve_tsp(dist, return_operation_summary=True)

    print(cost)
    print(' '.join(map(str, path)))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()