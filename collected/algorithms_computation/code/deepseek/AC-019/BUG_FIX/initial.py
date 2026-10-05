def min_cost_path(cost_matrix):
    """
    Find minimum cost path from top-left to bottom-right moving only right or down.
    
    Args:
        cost_matrix: 2D list of non-negative integers
        
    Returns:
        tuple: (minimum_cost, path) where path is list of (row, col) tuples
    """
    if not cost_matrix or not cost_matrix[0]:
        return 0, []
    
    rows = len(cost_matrix)
    cols = len(cost_matrix[0])
    
    # Initialize DP table and predecessor tracking
    dp = [[0] * cols for _ in range(rows)]
    pred = [[None] * cols for _ in range(rows)]
    
    # Base case
    dp[0][0] = cost_matrix[0][0]
    
    # Fill first row (can only come from left)
    for j in range(1, cols):
        dp[0][j] = dp[0][j-1] + cost_matrix[0][j]
        pred[0][j] = (0, j-1)  # from left
    
    # Fill first column (can only come from above)
    for i in range(1, rows):
        dp[i][0] = dp[i-1][0] + cost_matrix[i][0]
        pred[i][0] = (i-1, 0)  # from above
    
    # Fill rest of the table
    for i in range(1, rows):
        for j in range(1, cols):
            # Deterministic tie handling: prefer from above when equal
            if dp[i-1][j] <= dp[i][j-1]:
                dp[i][j] = dp[i-1][j] + cost_matrix[i][j]
                pred[i][j] = (i-1, j)  # from above
            else:
                dp[i][j] = dp[i][j-1] + cost_matrix[i][j]
                pred[i][j] = (i, j-1)  # from left
    
    # Reconstruct path by backtracking
    path = []
    current = (rows - 1, cols - 1)
    
    while current is not None:
        path.append(current)
        current = pred[current[0]][current[1]]
    
    # Reverse to get path from start to end
    path.reverse()
    
    return dp[rows-1][cols-1], path


def print_matrix_and_path(cost_matrix, min_cost, path):
    """Helper function to visualize the matrix and path."""
    print("Cost Matrix:")
    for row in cost_matrix:
        print("  ", row)
    
    print(f"\nMinimum Cost: {min_cost}")
    print(f"Path: {path}")
    
    # Create visualization
    rows = len(cost_matrix)
    cols = len(cost_matrix[0])
    path_set = set(path)
    
    print("\nPath Visualization (* = path, . = not in path):")
    for i in range(rows):
        row_str = "  "
        for j in range(cols):
            if (i, j) in path_set:
                row_str += f"[{cost_matrix[i][j]}]"
            else:
                row_str += f" {cost_matrix[i][j]} "
        print(row_str)


# Test cases
def test_min_cost_path():
    """Test the implementation with various cases."""
    
    print("=" * 60)
    print("Test Case 1: Simple 3x3 matrix")
    print("=" * 60)
    matrix1 = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]
    cost1, path1 = min_cost_path(matrix1)
    print_matrix_and_path(matrix1, cost1, path1)
    assert cost1 == 7, f"Expected 7, got {cost1}"
    assert path1[0] == (0, 0) and path1[-1] == (2, 2)
    
    print("\n" + "=" * 60)
    print("Test Case 2: 2x2 matrix with tie")
    print("=" * 60)
    matrix2 = [
        [1, 1],
        [1, 1]
    ]
    cost2, path2 = min_cost_path(matrix2)
    print_matrix_and_path(matrix2, cost2, path2)
    assert cost2 == 3, f"Expected 3, got {cost2}"
    # With tie-breaking preferring up, path should go down then right
    # Actually: (0,0) -> (0,1) -> (1,1) OR (0,0) -> (1,0) -> (1,1)
    # Our tie-breaking: at (1,1), dp[0][1]=2, dp[1][0]=2, prefer up (0,1)
    # So path: (0,0) -> (0,1) -> (1,1)
    assert path2 == [(0, 0), (0, 1), (1, 1)], f"Unexpected path: {path2}"
    
    print("\n" + "=" * 60)
    print("Test Case 3: Single cell")
    print("=" * 60)
    matrix3 = [[5]]
    cost3, path3 = min_cost_path(matrix3)
    print_matrix_and_path(matrix3, cost3, path3)
    assert cost3 == 5, f"Expected 5, got {cost3}"
    assert path3 == [(0, 0)]
    
    print("\n" + "=" * 60)
    print("Test Case 4: Single row")
    print("=" * 60)
    matrix4 = [[1, 2, 3, 4]]
    cost4, path4 = min_cost_path(matrix4)
    print_matrix_and_path(matrix4, cost4, path4)
    assert cost4 == 10, f"Expected 10, got {cost4}"
    assert path4 == [(0, 0), (0, 1), (0, 2), (0, 3)]
    
    print("\n" + "=" * 60)
    print("Test Case 5: Single column")
    print("=" * 60)
    matrix5 = [[1], [2], [3], [4]]
    cost5, path5 = min_cost_path(matrix5)
    print_matrix_and_path(matrix5, cost5, path5)
    assert cost5 == 10, f"Expected 10, got {cost5}"
    assert path5 == [(0, 0), (1, 0), (2, 0), (3, 0)]
    
    print("\n" + "=" * 60)
    print("Test Case 6: Larger matrix with multiple optimal paths")
    print("=" * 60)
    matrix6 = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    cost6, path6 = min_cost_path(matrix6)
    print_matrix_and_path(matrix6, cost6, path6)
    # Path should be (0,0) -> (0,1) -> (0,2) -> (1,2) -> (2,2) = 1+2+3+6+9 = 21
    # Or (0,0) -> (1,0) -> (2,0) -> (2,1) -> (2,2) = 1+4+7+8+9 = 29
    # Or (0,0) -> (0,1) -> (1,1) -> (1,2) -> (2,2) = 1+2+5+6+9 = 23
    # Best is 21
    assert cost6 == 21, f"Expected 21, got {cost6}"
    assert path6 == [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]
    
    print("\n" + "=" * 60)
    print("All test cases passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_min_cost_path()