def solve_tsp(dist_matrix: list[list[int | float]]) -> tuple[list[int], float | int]:
    """
    Solves the TSP using Held-Karp dynamic programming with deterministic tie-breaking.
    
    :param dist_matrix: N x N symmetric distance matrix (N <= 14).
    :return: Tuple containing (path, minimum_distance).
    """
    n = len(dist_matrix)
    if n == 0:
        return [], 0
    if n == 1:
        return [0, 0], 0

    full_mask = (1 << n) - 1

    # dp[mask][u] = (min_cost, predecessor)
    dp = {}

    # Base case: start at city 0
    dp[(1 << 0, 0)] = (0, -1)

    # Iterate through subset sizes from 2 to N
    for mask_size in range(2, n + 1):
        for mask in range(1, 1 << n):
            # Must include city 0 and have exactly `mask_size` bits set
            if not (mask & 1) or bin(mask).count('1') != mask_size:
                continue

            for v in range(1, n):
                if not (mask & (1 << v)):
                    continue

                prev_mask = mask ^ (1 << v)
                best_cost = float('inf')
                best_pred = -1

                # Try all predecessors u in ascending order for tie-breaking
                for u in range(n):
                    if u == v or not (prev_mask & (1 << u)):
                        continue

                    if (prev_mask, u) in dp:
                        cost = dp[(prev_mask, u)][0] + dist_matrix[u][v]
                        # Tie-breaker: strictly less than preferred; smaller predecessors checked first
                        if cost < best_cost:
                            best_cost = cost
                            best_pred = u

                if best_pred != -1:
                    dp[(mask, v)] = (best_cost, best_pred)

    # Find the optimal return step to city 0
    min_total_cost = float('inf')
    last_city = -1

    for u in range(1, n):
        if (full_mask, u) in dp:
            cost = dp[(full_mask, u)][0] + dist_matrix[u][0]
            if cost < min_total_cost:
                min_total_cost = cost
                last_city = u

    # Reconstruct the optimal cycle
    path = [0]
    curr_mask = full_mask
    curr_city = last_city

    reconstructed = []
    while curr_city != -1:
        reconstructed.append(curr_city)
        _, prev_city = dp[(curr_mask, curr_city)]
        curr_mask ^= (1 << curr_city)
        curr_city = prev_city

    reconstructed.reverse()
    path = reconstructed + [0]

    return path, min_total_cost


# Example Usage:
if __name__ == "__main__":
    matrix = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0]
    ]

    best_path, min_cost = solve_tsp(matrix)
    print("Optimal Path:", best_path)
    print("Minimum Cost:", min_cost)