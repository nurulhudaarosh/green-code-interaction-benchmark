def matrix_chain_order(p):
    """
    Computes the minimum scalar multiplication cost and optimal parenthesization
    for a chain of matrices with dimensions given by sequence p.
    
    Tie-breaking rule: Strictly picks the smallest split index k when costs are equal.
    """
    if not p or len(p) < 2:
        return 0, ""

    n = len(p) - 1  # Number of matrices

    if n == 1:
        return 0, "A1"

    # m[i][j]: minimum cost to multiply A_i through A_j
    # s[i][j]: optimal split index k for subchain A_i through A_j
    # 1-based indexing for matrices A_1 ... A_n
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    # Interval DP: l is the length of the matrix chain subproblem
    for l in range(2, n + 1):
        for i in range(1, n - l + 2):
            j = i + l - 1
            m[i][j] = float('inf')
            
            # Iterate k from i to j - 1 in strictly ascending order
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                
                # Strict inequality strictly enforces picking the smallest k on tie
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    # Reconstruct optimal parenthesization string
    def build_string(i, j):
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = build_string(i, k)
        right = build_string(k + 1, j)
        return f"({left}{right})"

    return m[1][n], build_string(1, n)


# Verification Test
if __name__ == "__main__":
    # Test case with identical dimensions to force ties across multiple split points
    test_p = [10, 10, 10, 10, 10]
    cost, parenthesization = matrix_chain_order(test_p)
    
    print(f"Dimensions: {test_p}")
    print(f"Minimum Cost: {cost}")
    print(f"Parenthesization: {parenthesization}")