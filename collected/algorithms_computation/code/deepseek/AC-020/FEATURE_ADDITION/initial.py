def solve_tsp(distance_matrix):
    """
    Solve TSP using Held-Karp subset DP.
    Returns (min_cost, optimal_path) where optimal_path starts and ends at 0.
    Ties prefer the smaller predecessor.
    """
    n = len(distance_matrix)
    
    # Edge case: single city
    if n == 1:
        return 0, [0, 0]
    
    # Edge case: two cities
    if n == 2:
        return distance_matrix[0][1] * 2, [0, 1, 0]
    
    INF = float('inf')
    FULL_MASK = (1 << n) - 1
    
    # dp[mask][i] = min cost to start at 0, visit cities in mask, end at i
    dp = [[INF] * n for _ in range(1 << n)]
    # parent[mask][i] = predecessor of i in optimal path for state (mask, i)
    parent = [[-1] * n for _ in range(1 << n)]
    
    # Base case
    dp[1][0] = 0
    
    # Iterate over all masks
    for mask in range(1, 1 << n):
        if not (mask & 1):  # city 0 must be in mask
            continue
        for i in range(n):
            if not (mask & (1 << i)):
                continue
            if dp[mask][i] == INF:
                continue
            # Try adding each unvisited city j
            for j in range(n):
                if mask & (1 << j):
                    continue
                new_mask = mask | (1 << j)
                new_cost = dp[mask][i] + distance_matrix[i][j]
                if new_cost < dp[new_mask][j]:
                    dp[new_mask][j] = new_cost
                    parent[new_mask][j] = i
                elif new_cost == dp[new_mask][j]:
                    # Tie: prefer smaller predecessor
                    if parent[new_mask][j] == -1 or i < parent[new_mask][j]:
                        parent[new_mask][j] = i
    
    # Find optimal final city (return to 0)
    best_cost = INF
    best_last = -1
    for i in range(1, n):
        if dp[FULL_MASK][i] == INF:
            continue
        total = dp[FULL_MASK][i] + distance_matrix[i][0]
        if total < best_cost:
            best_cost = total
            best_last = i
        elif total == best_cost:
            # Tie: prefer smaller predecessor
            # The predecessor of 0 in final step is best_last vs i
            if i < best_last:
                best_last = i
    
    # Reconstruct path
    path = []
    mask = FULL_MASK
    current = best_last
    while current != -1:
        path.append(current)
        prev = parent[mask][current]
        mask ^= (1 << current)
        current = prev
    
    path.reverse()
    path.append(0)  # return to start
    
    return best_cost, path


def main():
    import sys
    
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    idx = 0
    n = int(data[idx]); idx += 1
    
    # Read n x n distance matrix
    dist = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(int(data[idx]))
            idx += 1
        dist.append(row)
    
    cost, path = solve_tsp(dist)
    print(cost)
    print(' '.join(map(str, path)))


if __name__ == "__main__":
    main()