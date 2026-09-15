def matrix_chain_order(p):
    """
    Computes the minimum scalar multiplication cost and optimal parenthesization
    for a chain of matrices given their dimensions p.
    
    Tie-breaking rule: Equal-cost choices pick the smallest split index k.
    """
    n = len(p) - 1
    if n <= 0:
        return 0, ""
    if n == 1:
        return 0, "A1"

    # m[i][j]: minimum cost to multiply A_i...A_j
    # s[i][j]: optimal split point k for A_i...A_j
    # 1-based indexing used for matrices A_1 to A_n
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    # l is the chain length
    for l in range(2, n + 1):
        for i in range(1, n - l + 2):
            j = i + l - 1
            m[i][j] = float('inf')
            
            # Iterate k from i to j-1 (ensures smallest k is picked on ties)
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                if cost < m[i][j]:  # Strict inequality enforces smallest split index tie-breaker
                    m[i][j] = cost
                    s[i][j] = k

    def build_parentheses(i, j):
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = build_parentheses(i, k)
        right = build_parentheses(k + 1, j)
        return f"({left}{right})"

    min_cost = m[1][n]
    parenthesization = build_parentheses(1, n)
    
    return min_cost, parenthesization


# Example usage:
if __name__ == "__main__":
    # Example dimensions: Matrix A1 (10x30), A2 (30x5), A3 (5x60)
    dimensions = [10, 30, 5, 60]
    cost, structure = matrix_chain_order(dimensions)
    print(f"Minimum Cost: {cost}")
    print(f"Optimal Parenthesization: {structure}")