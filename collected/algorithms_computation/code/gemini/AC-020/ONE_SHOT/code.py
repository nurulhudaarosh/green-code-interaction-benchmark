def solve_tsp(dist_matrix):
    """
    Solves the Traveling Salesperson Problem using Held-Karp Dynamic Programming.
    
    :param dist_matrix: List[List[number]] - Complete symmetric distance matrix for N <= 14 cities.
    :return: Tuple[number, List[int]] - Minimum cost and optimal tour starting/ending at city 0.
    """
    n = len(dist_matrix)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0, 0]

    # Full mask with all cities visited
    full_mask = (1 << n) - 1

    # dp[mask][u] = min cost to visit cities in mask, ending at u
    # parent[mask][u] = predecessor city of u in the optimal path for state (mask, u)
    dp = {}
    parent = {}

    # Base case: start at city 0
    dp[(1, 0)] = 0

    # Iterate through all subset sizes from 1 to n
    for size in range(1, n):
        # Gather all valid masks of given size that include city 0
        current_states = [
            (mask, u) for (mask, u) in dp if bin(mask).count('1') == size
        ]

        for mask, u in current_states:
            cost = dp[(mask, u)]

            # Try visiting an unvisited city v
            for v in range(n):
                if not (mask & (1 << v)):
                    next_mask = mask | (1 << v)
                    new_cost = cost + dist_matrix[u][v]

                    if (next_mask, v) not in dp:
                        dp[(next_mask, v)] = new_cost
                        parent[(next_mask, v)] = u
                    else:
                        # Tie-breaking logic: prefer smaller predecessor u on equal cost
                        current_best_cost = dp[(next_mask, v)]
                        current_best_parent = parent[(next_mask, v)]

                        if new_cost < current_best_cost:
                            dp[(next_mask, v)] = new_cost
                            parent[(next_mask, v)] = u
                        elif new_cost == current_best_cost and u < current_best_parent:
                            parent[(next_mask, v)] = u

    # Find the optimal last city before returning to 0
    min_total_cost = float('inf')
    last_city = -1

    for u in range(1, n):
        if (full_mask, u) in dp:
            total_cost = dp[(full_mask, u)] + dist_matrix[u][0]
            if total_cost < min_total_cost:
                min_total_cost = total_cost
                last_city = u
            elif total_cost == min_total_cost and (last_city == -1 or u < last_city):
                last_city = u

    # Reconstruct the optimal path backward
    path = []
    curr_mask = full_mask
    curr_city = last_city

    while curr_city != 0:
        path.append(curr_city)
        prev_city = parent[(curr_mask, curr_city)]
        curr_mask ^= (1 << curr_city)
        curr_city = prev_city

    path.append(0)
    path.reverse()
    path.append(0)  # Complete the cycle back to 0

    return min_total_cost, path


# Example Execution
if __name__ == "__main__":
    # Sample symmetric distance matrix for 4 cities
    example_matrix = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0]
    ]

    min_cost, tour = solve_tsp(example_matrix)
    print(f"Minimum Tour Cost: {min_cost}")
    print(f"Optimal Tour Path: {tour}")