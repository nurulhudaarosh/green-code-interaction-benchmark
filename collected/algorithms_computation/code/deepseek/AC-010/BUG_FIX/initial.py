import sys

def matrix_chain_order(p):
    """
    Find minimum scalar multiplication cost and parenthesization for matrix chain.
    
    Args:
        p: List of dimensions where matrix i has dimensions p[i-1] x p[i]
    
    Returns:
        Tuple of (minimum cost, parenthesization string)
    """
    n = len(p) - 1  # number of matrices
    
    # dp[i][j] = minimum cost to multiply matrices i..j (1-indexed)
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    
    # split[i][j] = split index that gives minimum cost for matrices i..j
    split = [[0] * (n + 1) for _ in range(n + 1)]
    
    # length of chain: from 2 to n
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            # Try all possible split positions k where i <= k < j
            # k is the last matrix in the left subchain
            for k in range(i, j):
                cost = dp[i][k] + dp[k+1][j] + p[i-1] * p[k] * p[j]
                
                # Use < for tie-breaking (smaller split index when equal)
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k
    
    # Build parenthesization string
    def build_parenthesization(i, j):
        if i == j:
            return f"A{i}"
        else:
            k = split[i][j]
            left = build_parenthesization(i, k)
            right = build_parenthesization(k+1, j)
            return f"({left} x {right})"
    
    # For n = 1, special case
    if n == 1:
        return 0, "A1"
    
    min_cost = dp[1][n]
    parenthesization = build_parenthesization(1, n)
    
    return min_cost, parenthesization


def solve_matrix_chain():
    """
    Read input, compute minimum cost and parenthesization, print results.
    Input format: First line contains n (number of matrices)
    Second line contains n+1 integers: dimensions p0, p1, ..., pn
    """
    # Read all input from stdin
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    # Parse input
    try:
        n = int(data[0])
        dimensions = list(map(int, data[1:1+n+1]))
        
        if len(dimensions) != n + 1:
            print("Error: Invalid number of dimensions")
            return
        
        # Validate dimensions are positive
        if any(d <= 0 for d in dimensions):
            print("Error: Dimensions must be positive integers")
            return
        
        min_cost, parenthesization = matrix_chain_order(dimensions)
        
        print(f"Minimum cost: {min_cost}")
        print(f"Parenthesization: {parenthesization}")
        
    except ValueError:
        print("Error: Invalid input format")


if __name__ == "__main__":
    solve_matrix_chain()