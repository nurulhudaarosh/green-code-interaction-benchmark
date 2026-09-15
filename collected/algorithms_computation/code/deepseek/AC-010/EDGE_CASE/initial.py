def matrix_chain_order(p):
    """
    Find minimum scalar multiplication cost and parenthesization for matrix chain.
    
    Args:
        p: List of dimensions where matrix i has dimensions p[i-1] x p[i]
    
    Returns:
        tuple: (min_cost, parenthesization_string)
    """
    n = len(p) - 1  # number of matrices
    
    # dp[i][j] = minimum cost to multiply matrices i through j (0-indexed)
    dp = [[0] * n for _ in range(n)]
    
    # split[i][j] = optimal split position for matrices i through j
    split = [[0] * n for _ in range(n)]
    
    # length of chain (number of matrices)
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            # Try all possible split positions
            for k in range(i, j):
                cost = dp[i][k] + dp[k+1][j] + p[i] * p[k+1] * p[j+1]
                
                # Use smallest split index when costs are equal
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k
    
    # Build parenthesization string
    def build_parenthesization(i, j):
        if i == j:
            return f"M{i+1}"
        k = split[i][j]
        left = build_parenthesization(i, k)
        right = build_parenthesization(k+1, j)
        return f"({left} × {right})"
    
    if n == 0:
        return 0, ""
    elif n == 1:
        return 0, "M1"
    
    min_cost = dp[0][n-1]
    parenthesization = build_parenthesization(0, n-1)
    
    return min_cost, parenthesization


def solve_matrix_chain():
    """
    Read input, compute minimum cost and parenthesization, print results.
    """
    try:
        # Read dimensions
        line = input().strip()
        while line == '':
            line = input().strip()
        
        p = list(map(int, line.split()))
        
        # Validate input
        if len(p) < 2:
            print("0")
            print("")
            return
        
        min_cost, parenthesization = matrix_chain_order(p)
        
        print(min_cost)
        print(parenthesization)
        
    except EOFError:
        return


if __name__ == "__main__":
    solve_matrix_chain()