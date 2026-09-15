def matrix_chain_order(p: list[int]) -> tuple[int, str]:
    """
    Computes the minimum scalar multiplication cost and the optimal parenthesization
    for a chain of matrices defined by dimensions p.
    
    Args:
        p: List of dimensions where matrix A_i has dimension p[i-1] x p[i].
        
    Returns:
        A tuple of (minimum_cost, parenthesized_expression_string).
    """
    n = len(p) - 1
    if n == 0:
        return 0, ""
    if n == 1:
        return 0, "A1"

    # m[i][j] stores the minimum cost of multiplying A_i...A_j
    # s[i][j] stores the optimal split index k
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    # L is the chain length
    for L in range(2, n + 1):
        for i in range(1, n - L + 2):
            j = i + L - 1
            m[i][j] = float('inf')
            
            # Evaluate potential split indices k
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                
                # Strict inequality ensures equal-cost choices keep the smallest split index k
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    def construct_parenthesization(i: int, j: int) -> str:
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = construct_parenthesization(i, k)
        right = construct_parenthesization(k + 1, j)
        return f"({left}{right})"

    return m[1][n], construct_parenthesization(1, n)


# Example usage
if __name__ == "__main__":
    # Matrices: A1 (10x30), A2 (30x5), A3 (5x60)
    dimensions = [10, 30, 5, 60]
    min_cost, expression = matrix_chain_order(dimensions)
    print(f"Minimum Scalar Multiplications: {min_cost}")
    print(f"Optimal Parenthesization: {expression}")