def solve_tsp(dist_matrix):
    """
    Solves the Traveling Salesperson Problem using the Held-Karp algorithm.
    
    Parameters:
        dist_matrix (list of list of float/int): Symmetric N x N distance matrix.
        
    Returns:
        tuple: (min_cost, tour) where:
            - min_cost is the total distance of the optimal cycle.
            - tour is a list of city indices starting and ending at 0.
    """
    n = len(dist_matrix)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, [0, 0]

    # dp[(mask, i)] = (min_cost, predecessor)
    # mask is a bitmask representing the subset of visited cities.
    dp = {}
    
    # Base case: Starting at city 0 with mask 1 (0b00...001)
    dp[(1, 0)] = (0, -1)

    # Iterate through subset sizes from 2 to N
    for mask_size in range(2, n + 1):
        # Generate all bitmasks of length n with 'mask_size' bits set, including bit 0
        for mask in range(1, 1 << n):
            if not (mask & 1):
                continue
            # Check if popcount equals mask_size
            if bin(mask).count('1') != mask_size:
                continue

            for i in range(1, n):
                if not (mask & (1 << i)):
                    continue
                
                prev_mask = mask ^ (1 << i)
                best_cost = float('inf')
                best_pred = -1

                for j in range(n):
                    if not (prev_mask & (1 << j)):
                        continue
                    if (prev_mask, j) in dp:
                        cost = dp[(prev_mask, j)][0] + dist_matrix[j][i]
                        # Tie-breaking: if costs are equal, prefer smaller predecessor j
                        if cost < best_cost:
                            best_cost = cost
                            best_pred = j
                        elif cost == best_cost and j < best_pred:
                            best_pred = j

                if best_pred != -1:
                    dp[(mask, i)] = (best_cost, best_pred)

    # Find optimal last city before returning to city 0
    full_mask = (1 << n) - 1
    min_total_cost = float('inf')
    best_last_city = -1

    for j in range(1, n):
        if (full_mask, j) in dp:
            cost = dp[(full_mask, j)][0] + dist_matrix[j][0]
            if cost < min_total_cost:
                min_total_cost = cost
                best_last_city = j
            elif cost == min_total_cost and j < best_last_city:
                best_last_city = j

    # Reconstruct the tour path backwards
    curr_mask = full_mask
    curr_city = best_last_city
    rev_path = []

    while curr_city != -1:
        rev_path.append(curr_city)
        next_city = dp[(curr_mask, curr_city)][1]
        curr_mask = curr_mask ^ (1 << curr_city)
        curr_city = next_city

    tour = rev_path[::-1] + [0]
    return min_total_cost, tour


# Example Usage:
if __name__ == "__main__":
    # Symmetric 4-city example distance matrix
    dist = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0]
    ]

    min_cost, path = solve_tsp(dist)
    print(f"Minimum Cost: {min_cost}")
    print(f"Optimal Tour: {path}")