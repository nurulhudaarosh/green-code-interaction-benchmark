def solve_tsp(dist_matrix):
    """
    Solves the TSP using Held-Karp Dynamic Programming.
    
    :param dist_matrix: List[List[int/float]], symmetric matrix of sizes N x N (N <= 14).
    :return: Tuple (min_cost, path) where path is a list of city indices starting and ending at 0.
    """
    N = len(dist_matrix)
    if N == 0:
        return 0, []
    if N == 1:
        return 0, [0, 0]

    num_states = 1 << N
    INF = float('inf')

    # dp[S][u] = min cost to start at 0, visit all cities in bitmask S, ending at u
    dp = [[INF] * N for _ in range(num_states)]
    # parent[S][u] stores predecessor of u in subset S for path reconstruction
    parent = [[-1] * N for _ in range(num_states)]

    # Base case: starting at city 0
    dp[1][0] = 0

    # Iterate over all subset sizes from 2 to N
    for size in range(2, N + 1):
        for S in range(1, num_states):
            # Must include city 0 and match current size
            if not (S & 1) or bin(S).count('1') != size:
                continue

            # Target last city v in subset S (v != 0)
            for v in range(1, N):
                if not (S & (1 << v)):
                    continue

                prev_S = S ^ (1 << v)
                best_cost = INF
                best_pred = -1

                # Search for best predecessor u in prev_S
                for u in range(N):
                    if prev_S & (1 << u):
                        cost = dp[prev_S][u] + dist_matrix[u][v]
                        # Tie-breaking: strict < naturally prefers smaller u when iterating 0..N-1
                        if cost < best_cost:
                            best_cost = cost
                            best_pred = u

                dp[S][v] = best_cost
                parent[S][v] = best_pred

    # Complete the cycle by returning to city 0 from the last city u
    full_mask = num_states - 1
    min_total_cost = INF
    last_city = -1

    for u in range(1, N):
        cost = dp[full_mask][u] + dist_matrix[u][0]
        if cost < min_total_cost:
            min_total_cost = cost
            last_city = u

    # Reconstruct the path backwards
    path = []
    curr_mask = full_mask
    curr_city = last_city

    while curr_city != -1:
        path.append(curr_city)
        next_city = parent[curr_mask][curr_city]
        curr_mask ^= (1 << curr_city)
        curr_city = next_city

    path.reverse()
    path.append(0)  # Close the loop at city 0

    return min_total_cost, path


# Example Usage:
if __name__ == "__main__":
    # Sample symmetric 4-city distance matrix
    dist = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0]
    ]

    min_cost, tour = solve_tsp(dist)
    print(f"Minimum Tour Cost: {min_cost}")
    print(f"Optimal Path: {' -> '.join(map(str, tour))}")