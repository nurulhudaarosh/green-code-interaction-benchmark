def min_cost_path(grid):
    """
    Finds the minimum cost path in a grid moving only right or down.
    
    Args:
        grid (List[List[int/float]]): Non-negative cost matrix.
        
    Returns:
        Tuple[Union[int, float], List[Tuple[int, int]]]:
            - Minimum cumulative path cost.
            - Deterministic list of coordinate tuples representing the path.
    """
    if not grid or not grid[0]:
        return 0, []
    
    m, n = len(grid), len(grid[0])
    
    # DP table to store minimum costs to reach each cell
    dp = [[0] * n for _ in range(m)]
    
    # Initialize start cell
    dp[0][0] = grid[0][0]
    
    # Initialize first column (can only come from above)
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + grid[i][0]
        
    # Initialize first row (can only come from the left)
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + grid[0][j]
        
    # Populate the rest of the DP table
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = grid[i][j] + min(dp[i - 1][j], dp[i][j - 1])
            
    # Deterministic Backtracking to reconstruct the path
    path = []
    curr_r, curr_c = m - 1, n - 1
    
    while curr_r > 0 or curr_c > 0:
        path.append((curr_r, curr_c))
        
        if curr_r == 0:
            curr_c -= 1
        elif curr_c == 0:
            curr_r -= 1
        else:
            # Deterministic tie-handling: favor moving UP (curr_r - 1) over LEFT (curr_c - 1)
            if dp[curr_r - 1][curr_c] <= dp[curr_r][curr_c - 1]:
                curr_r -= 1
            else:
                curr_c -= 1
                
    path.append((0, 0))
    path.reverse()  # Reverse path to go from (0, 0) to (m-1, n-1)
    
    min_cost = dp[m - 1][n - 1]
    return min_cost, path


# Example usage
if __name__ == "__main__":
    matrix = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]
    
    cost, path_coords = min_cost_path(matrix)
    print("Minimum Cost:", cost)
    print("Optimal Path:", path_coords)