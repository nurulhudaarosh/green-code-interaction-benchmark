def solve_tsp(dist_matrix):
    """
    Solves TSP using Held-Karp Dynamic Programming with deterministic tie-breaking.
    Prefers smaller predecessor indices whenever path costs are equal.

    :param dist_matrix: List[List[int/float]], symmetric distance matrix (N <= 14).
    :return: Tuple (min_cost, path) where path is a list of city indices starting and ending at 0.
    """
    N = len(dist_matrix)
    if N == 0:
        return 0, []
    if N == 1:
        return 0, [0, 0]

    num_states = 1 << N
    INF = float('inf')

    # dp[S][u]: min cost to start at 0, visit subset S, end at u
    dp = [[INF] * N for _ in range(num_states)]
    # parent[S][u]: predecessor of u in subset S
    parent = [[-1] * N for _ in range(num_states)]

    # Base case: start at city 0
    dp[1][0] = 0

    # Fill DP table by subset size
    for size in range(2, N + 1):
        for S in range(1, num_states):
            if not (S & 1) or bin(S).count('1') != size:
                continue

            for v in range(1, N):
                if not (S & (1 << v)):
                    continue

                prev_S = S ^ (1 << v)
                best_cost = INF
                best_pred = -1

                # Search predecessors u in order 0..N-1
                # Strict '<' ensures the smaller index u is retained on ties
                for u in range(N):
                    if prev_S & (1 << u):
                        cost = dp[prev_S][u] + dist_matrix[u][v]
                        if cost < best_cost:
                            best_cost = cost
                            best_pred = u

                dp[S][v] = best_cost
                parent[S][v] = best_pred

    # Complete the cycle by returning to city 0
    full_mask = num_states - 1
    min_total_cost = INF
    last_city = -1

    # Search last cities u in order 1..N-1
    # Strict '<' ensures the smaller index u is retained on ties
    for u in range(1, N):
        cost = dp[full_mask][u] + dist_matrix[u][0]
        if cost < min_total_cost:
            min_total_cost = cost
            last_city = u

    # Reconstruct the optimal tour
    path = []
    curr_mask = full_mask
    curr_city = last_city

    while curr_city != -1:
        path.append(curr_city)
        next_city = parent[curr_mask][curr_city]
        curr_mask ^= (1 << curr_city)
        curr_city = next_city

    path.reverse()
    path.append(0)

    return min_total_cost, path