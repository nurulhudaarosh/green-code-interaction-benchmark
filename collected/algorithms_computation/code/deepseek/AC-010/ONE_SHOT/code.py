def matrix_chain_order(p):
    """
    Find minimum scalar multiplication cost and optimal parenthesization
    for matrix chain with dimensions p0..pn.
    
    Args:
        p: list of dimensions where matrix i has dimensions p[i-1] x p[i]
    
    Returns:
        (min_cost, parenthesization_string)
    """
    n = len(p) - 1  # number of matrices
    
    # m[i][j] = minimum cost to multiply matrices i..j (1-indexed)
    # s[i][j] = split point for optimal parenthesization of matrices i..j
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]
    
    # l = chain length
    for l in range(2, n + 1):
        for i in range(1, n - l + 2):
            j = i + l - 1
            m[i][j] = float('inf')
            
            # Try all possible split points k
            # Equal-cost choices use the smallest split index
            for k in range(i, j):
                cost = m[i][k] + m[k+1][j] + p[i-1] * p[k] * p[j]
                
                # Use < for smallest split index on equal costs
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k
    
    # Build parenthesization string
    def get_parenthesization(i, j):
        if i == j:
            return f"A{i}"
        else:
            k = s[i][j]
            left = get_parenthesization(i, k)
            right = get_parenthesization(k+1, j)
            return f"({left} × {right})"
    
    if n == 0:
        return 0, ""
    elif n == 1:
        return 0, "A1"
    else:
        return m[1][n], get_parenthesization(1, n)


def solve_matrix_chain():
    """
    Read input, solve matrix chain problem, and output results.
    """
    # Read dimensions
    try:
        line = input().strip()
        if not line:
            return
        p = list(map(int, line.split()))
    except EOFError:
        return
    
    # Validate input
    if len(p) < 2:
        print(0)
        print("")
        return
    
    n = len(p) - 1
    min_cost, parenthesization = matrix_chain_order(p)
    
    print(min_cost)
    print(parenthesization)


if __name__ == "__main__":
    solve_matrix_chain()