def min_cost_path(cost_matrix):
    """
    Find minimum cost path from top-left to bottom-right.
    Can only move right or down.
    
    Args:
        cost_matrix: 2D list of non-negative integers
    
    Returns:
        tuple: (min_cost, path) where path is list of (row, col) tuples
    """
    if not cost_matrix or not cost_matrix[0]:
        return 0, []
    
    rows = len(cost_matrix)
    cols = len(cost_matrix[0])
    
    # dp[i][j] = minimum cost to reach cell (i, j)
    dp = [[0] * cols for _ in range(rows)]
    
    # predecessor[i][j] = (prev_row, prev_col) or None for start
    predecessor = [[None] * cols for _ in range(rows)]
    
    # Initialize first cell
    dp[0][0] = cost_matrix[0][0]
    
    # Fill first row (can only come from left)
    for j in range(1, cols):
        dp[0][j] = dp[0][j-1] + cost_matrix[0][j]
        predecessor[0][j] = (0, j-1)
    
    # Fill first column (can only come from above)
    for i in range(1, rows):
        dp[i][0] = dp[i-1][0] + cost_matrix[i][0]
        predecessor[i][0] = (i-1, 0)
    
    # Fill rest of the table
    for i in range(1, rows):
        for j in range(1, cols):
            from_above = dp[i-1][j]
            from_left = dp[i][j-1]
            
            # Deterministic tie-breaking: prefer "from above" when equal
            if from_above <= from_left:
                dp[i][j] = cost_matrix[i][j] + from_above
                predecessor[i][j] = (i-1, j)
            else:
                dp[i][j] = cost_matrix[i][j] + from_left
                predecessor[i][j] = (i, j-1)
    
    # Reconstruct path from bottom-right to top-left
    path = []
    current = (rows - 1, cols - 1)
    
    while current is not None:
        path.append(current)
        current = predecessor[current[0]][current[1]]
    
    # Reverse to get path from start to end
    path.reverse()
    
    return dp[rows-1][cols-1], path


def print_solution(cost_matrix):
    """Helper function to display the solution nicely."""
    min_cost, path = min_cost_path(cost_matrix)
    
    print("Cost Matrix:")
    for row in cost_matrix:
        print("  ", row)
    
    print(f"\nMinimum Cost: {min_cost}")
    print(f"Path: {path}")
    
    # Visualize the path on the matrix
    print("\nPath visualization (X marks the path):")
    path_set = set(path)
    for i in range(len(cost_matrix)):
        row_str = "  "
        for j in range(len(cost_matrix[0])):
            if (i, j) in path_set:
                row_str += f"[{cost_matrix[i][j]}]"
            else:
                row_str += f" {cost_matrix[i][j]} "
            if j < len(cost_matrix[0]) - 1:
                row_str += " "
        print(row_str)
    
    return min_cost, path


# Test cases
if __name__ == "__main__":
    print("=" * 50)
    print("Test Case 1: Simple 3x3 matrix")
    print("=" * 50)
    matrix1 = [
        [1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]
    ]
    print_solution(matrix1)
    
    print("\n" + "=" * 50)
    print("Test Case 2: Matrix with ties (deterministic handling)")
    print("=" * 50)
    matrix2 = [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]
    ]
    print_solution(matrix2)
    
    print("\n" + "=" * 50)
    print("Test Case 3: Single cell")
    print("=" * 50)
    matrix3 = [[5]]
    print_solution(matrix3)
    
    print("\n" + "=" * 50)
    print("Test Case 4: Single row")
    print("=" * 50)
    matrix4 = [[1, 2, 3, 4]]
    print_solution(matrix4)
    
    print("\n" + "=" * 50)
    print("Test Case 5: Single column")
    print("=" * 50)
    matrix5 = [[1], [2], [3], [4]]
    print_solution(matrix5)
    
    print("\n" + "=" * 50)
    print("Test Case 6: Larger matrix")
    print("=" * 50)
    matrix6 = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16]
    ]
    print_solution(matrix6)