def solve_tsp(distance_matrix):
    """
    Solve TSP using Held-Karp algorithm.
    
    Args:
        distance_matrix: n x n symmetric distance matrix
    
    Returns:
        tuple: (minimum_cost, optimal_tour)
        optimal_tour is a list starting and ending at 0
    """
    n = len(distance_matrix)
    
    if n == 1:
        return 0, [0, 0]
    if n == 2:
        cost = distance_matrix[0][1] + distance_matrix[1][0]
        return cost, [0, 1, 0]
    
    # dp[mask][i] = min cost to start at 0, visit cities in mask, end at i
    # mask always includes bit 0 (city 0)
    full_mask = (1 << n) - 1
    INF = float('inf')
    
    # Initialize DP table
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]
    
    # Base case: only city 0 visited, at city 0
    dp[1][0] = 0
    
    # Iterate over all masks
    for mask in range(1 << n):
        # Skip masks that don't include city 0
        if not (mask & 1):
            continue
        
        # For each ending city i in mask
        for i in range(n):
            if not (mask & (1 << i)):
                continue
            if dp[mask][i] == INF:
                continue
            
            # Try to add each unvisited city j
            for j in range(n):
                if mask & (1 << j):
                    continue
                
                new_mask = mask | (1 << j)
                new_cost = dp[mask][i] + distance_matrix[i][j]
                
                if new_cost < dp[new_mask][j]:
                    dp[new_mask][j] = new_cost
                    parent[new_mask][j] = i
                elif new_cost == dp[new_mask][j]:
                    # Tie-breaking: prefer smaller predecessor
                    if parent[new_mask][j] == -1 or i < parent[new_mask][j]:
                        parent[new_mask][j] = i
    
    # Find optimal final city
    min_cost = INF
    best_last = -1
    
    for i in range(1, n):
        if dp[full_mask][i] == INF:
            continue
        total_cost = dp[full_mask][i] + distance_matrix[i][0]
        
        if total_cost < min_cost:
            min_cost = total_cost
            best_last = i
        elif total_cost == min_cost:
            # Tie-breaking: prefer smaller predecessor (which is i, the last city)
            if best_last == -1 or i < best_last:
                best_last = i
    
    # Reconstruct tour
    tour = []
    mask = full_mask
    current = best_last
    
    while current != -1:
        tour.append(current)
        prev = parent[mask][current]
        mask = mask ^ (1 << current)
        current = prev
    
    tour.reverse()
    tour.append(0)  # Return to start
    
    return min_cost, tour


def main():
    """Main function to read input and output solution."""
    import sys
    
    # Read all input
    data = sys.stdin.read().strip().split()
    
    if not data:
        return
    
    idx = 0
    n = int(data[idx]); idx += 1
    
    # Read distance matrix
    distance_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(int(data[idx]))
            idx += 1
        distance_matrix.append(row)
    
    # Validate symmetry (optional but good practice)
    for i in range(n):
        for j in range(n):
            if distance_matrix[i][j] != distance_matrix[j][i]:
                print("Error: Distance matrix is not symmetric")
                return
    
    # Solve TSP
    min_cost, tour = solve_tsp(distance_matrix)
    
    # Output results
    print(f"Minimum cost: {min_cost}")
    print(f"Optimal tour: {' -> '.join(map(str, tour))}")


if __name__ == "__main__":
    main()