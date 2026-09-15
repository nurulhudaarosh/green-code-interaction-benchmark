def knapsack(indices, weights, values, capacity):
    n = len(indices)
    # dp[w] = max value for exact capacity w
    dp = [-10**18] * (capacity + 1)
    dp[0] = 0

    for i in range(n):
        w = weights[i]
        v = values[i]
        for cap in range(capacity, w - 1, -1):
            if dp[cap - w] + v > dp[cap]:
                dp[cap] = dp[cap - w] + v

    # Find the best total value over all capacities <= capacity
    best_val = max(dp)
    # Find the smallest capacity that achieves best_val (to help reconstruction)
    best_cap = 0
    for cap in range(capacity + 1):
        if dp[cap] == best_val:
            best_cap = cap
            break

    # Reconstruct lexicographically smallest index list
    selected = []
    rem_cap = best_cap
    for i in range(n):
        w = weights[i]
        v = values[i]
        if w <= rem_cap and dp[rem_cap] == dp[rem_cap - w] + v:
            selected.append(indices[i])
            rem_cap -= w

    return selected


def solve_knapsack(weights, values, capacity):
    """
    Returns the list of original indices (0-based) of items selected
    to maximize total value under capacity.
    Ties are broken by lexicographically smallest index list.
    """
    n = len(weights)
    indices = list(range(n))
    return knapsack(indices, weights, values, capacity)