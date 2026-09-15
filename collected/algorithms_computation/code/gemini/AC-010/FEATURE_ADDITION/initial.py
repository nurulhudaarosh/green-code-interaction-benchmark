def matrix_chain_order(p):
    """
    Computes the minimum scalar multiplication cost and optimal parenthesization.
    
    :param p: List of dimensions where matrix M_i has dimension p[i-1] x p[i].
    :return: Tuple (min_cost, parenthesized_expression_string)
    """
    n = len(p) - 1
    if n <= 0:
        return 0, ""
    if n == 1:
        return 0, "A1"

    # m[i][j] stores the minimum multiplication cost for M_i...M_j
    # s[i][j] stores the split index k that achieves this minimum cost
    # Using 1-based indexing for convenience
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    # L is the chain length
    for L in range(2, n + 1):
        for i in range(1, n - L + 2):
            j = i + L - 1
            m[i][j] = float('inf')
            
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                
                # Dynamic Programming update: strictly smaller cost updates best.
                # Since k loops in increasing order, using '<' automatically breaks
                # ties in favor of the smallest split index k.
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    def construct_parenthesization(i, j):
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = construct_parenthesization(i, k)
        right = construct_parenthesization(k + 1, j)
        return f"({left} {right})"

    min_cost = m[1][n]
    expression = construct_parenthesization(1, n)
    return min_cost, expression


if __name__ == "__main__":
    # Example dimensions for matrices A1 (10x30), A2 (30x5), A3 (5x60)
    dimensions = [10, 30, 5, 60]
    cost, expr = matrix_chain_order(dimensions)
    print(f"Minimum Scalar Multiplications: {cost}")
    print(f"Optimal Parenthesization: {expr}")