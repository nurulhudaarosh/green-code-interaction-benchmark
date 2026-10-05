def solve_tsp_held_karp(dist_matrix):
    """
    Solve TSP using Held-Karp algorithm.
    Returns (min_cost, optimal_tour)
    """
    n = len(dist_matrix)
    
    if n == 1:
        return 0, [0, 0]
    
    # dp[mask][i] = min cost to start at 0, visit cities in mask, end at i
    # parent[mask][i] = predecessor of i in the optimal path for this state
    dp = [[float('inf')] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]
    
    # Base case: only city 0 visited, ending at city 0
    dp[1][0] = 0
    
    # Process all subsets
    for mask in range(1 << n):
        # Skip if city 0 not in mask
        if not (mask & 1):
            continue
            
        for i in range(n):
            if not (mask & (1 << i)):  # i not in mask
                continue
            if dp[mask][i] == float('inf'):
                continue
                
            # Try adding each unvisited city j
            for j in range(n):
                if mask & (1 << j):  # j already visited
                    continue
                    
                new_mask = mask | (1 << j)
                new_cost = dp[mask][i] + dist_matrix[i][j]
                
                # Update if better, or if equal and smaller predecessor
                if (new_cost < dp[new_mask][j] or 
                    (new_cost == dp[new_mask][j] and i < parent[new_mask][j])):
                    dp[new_mask][j] = new_cost
                    parent[new_mask][j] = i
    
    # Find optimal tour by checking all possible last cities
    full_mask = (1 << n) - 1
    min_cost = float('inf')
    last_city = -1
    
    for i in range(1, n):  # i != 0 (we end at i, then return to 0)
        if dp[full_mask][i] == float('inf'):
            continue
            
        total_cost = dp[full_mask][i] + dist_matrix[i][0]
        
        # Update if better, or if equal and smaller predecessor
        if (total_cost < min_cost or 
            (total_cost == min_cost and i < last_city)):
            min_cost = total_cost
            last_city = i
    
    # Reconstruct the path
    if last_city == -1:
        return float('inf'), []
    
    path = []
    mask = full_mask
    current = last_city
    
    while current != -1:
        path.append(current)
        prev = parent[mask][current]
        mask ^= (1 << current)  # Remove current from mask
        current = prev
    
    path.reverse()
    path.append(0)  # Return to start
    
    return min_cost, path


def main():
    """Main function to handle input and output."""
    import sys
    
    # Read all input
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    # Parse number of cities
    n = int(data[0])
    
    # Parse distance matrix
    dist_matrix = []
    idx = 1
    for i in range(n):
        row = []
        for j in range(n):
            row.append(int(data[idx]))
            idx += 1
        dist_matrix.append(row)
    
    # Solve TSP
    min_cost, tour = solve_tsp_held_karp(dist_matrix)
    
    # Output results
    print(f"Minimum cost: {min_cost}")
    print(f"Optimal tour: {' -> '.join(map(str, tour))}")


if __name__ == "__main__":
    main()