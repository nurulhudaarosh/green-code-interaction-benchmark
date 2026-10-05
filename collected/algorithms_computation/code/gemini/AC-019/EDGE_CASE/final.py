def min_cost_path(grid):
    """
    Finds the minimum cost path in a non-negative cost matrix moving only right or down.
    Handles boundary limits (empty grids, 1x1, 1xn, mx1).
    
    Args:
        grid (List[List[Union[int, float]]]): Matrix of non-negative costs.
        
    Returns:
        Tuple[Union[int, float], List[Tuple[int, int]]]:
            - Minimum cumulative cost.
            - Deterministic path coordinate sequence from (0,0) to (m-1,n-1).
    """
    # Edge case: empty grid or empty inner lists
    if not grid or not grid[0]:
        return 0, []
    
    m, n = len(grid), len(grid[0])
    
    # DP matrix creation
    dp = [[0] * n for _ in range(m)]
    
    # Base case: starting point
    dp[0][0] = grid[0][0]
    
    # Initialize first column
    for i in range(1, m):
        dp[i][0] = dp[i - 1][0] + grid[i][0]
        
    # Initialize first row
    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + grid[0][j]
        
    # Populate DP table
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = grid[i][j] + min(dp[i - 1][j], dp[i][j - 1])
            
    # Deterministic Backtracking
    path = []
    curr_r, curr_c = m - 1, n - 1
    
    while curr_r > 0 or curr_c > 0:
        path.append((curr_r, curr_c))
        
        if curr_r == 0:
            curr_c -= 1
        elif curr_c == 0:
            curr_r -= 1
        else:
            # Deterministic tie-handling: favor UP (curr_r - 1) over LEFT (curr_c - 1)
            if dp[curr_r - 1][curr_c] <= dp[curr_r][curr_c - 1]:
                curr_r -= 1
            else:
                curr_c -= 1
                
    path.append((0, 0))
    path.reverse()
    
    return dp[m - 1][n - 1], path


# Comprehensive Boundary Unit Tests
def run_tests():
    # Test 1: Standard 3x3 Grid
    grid1 = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]
    cost1, path1 = min_cost_path(grid1)
    assert cost1 == 7
    assert path1 == [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]

    # Test 2: 1x1 Boundary Limit
    grid2 = [[5]]
    cost2, path2 = min_cost_path(grid2)
    assert cost2 == 5
    assert path2 == [(0, 0)]

    # Test 3: 1xN (Single Row) Boundary Limit
    grid3 = [[2, 3, 4, 1]]
    cost3, path3 = min_cost_path(grid3)
    assert cost3 == 10
    assert path3 == [(0, 0), (0, 1), (0, 2), (0, 3)]

    # Test 4: Mx1 (Single Column) Boundary Limit
    grid4 = [[1], [4], [2]]
    cost4, path4 = min_cost_path(grid4)
    assert cost4 == 7
    assert path4 == [(0, 0), (1, 0), (2, 0)]

    # Test 5: Empty Input
    cost5, path5 = min_cost_path([])
    assert cost5 == 0 and path5 == []

    # Test 6: Zero-Cost Matrix (Deterministic Tie-Breaker Test)
    grid6 = [
        [0, 0],
        [0, 0]
    ]
    cost6, path6 = min_cost_path(grid6)
    assert cost6 == 0
    # Equal costs favor UP over LEFT during backtrack, giving (0,0) -> (1,0) -> (1,1)
    assert path6 == [(0, 0), (1, 0), (1, 1)]

    print("All boundary and deterministic tests passed successfully!")


if __name__ == "__main__":
    run_tests()