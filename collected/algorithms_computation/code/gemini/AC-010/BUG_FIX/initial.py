def matrix_chain_order(p: list[int]) -> tuple[int, str]:
    """
    Computes the minimum scalar multiplication cost and optimal parenthesization
    for a chain of matrices with given dimensions p.
    
    Tie-breaking rule: Smallest split index k is chosen on equal cost.
    """
    n = len(p) - 1
    if n <= 0:
        return 0, ""
    if n == 1:
        return 0, "A1"

    # m[i][j] stores the minimum cost to multiply A_i...A_j
    # s[i][j] stores the split index k that achieves the minimum cost
    # Using 1-based indexing for matrix identifiers
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    # L is the chain length
    for L in range(2, n + 1):
        for i in range(1, n - L + 2):
            j = i + L - 1
            m[i][j] = float('inf')
            
            # Iterate split index k in ascending order
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                
                # Strict inequality ensures tie-breaker picks the smallest split index k
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    def build_parenthesization(i: int, j: int) -> str:
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = build_parenthesization(i, k)
        right = build_parenthesization(k + 1, j)
        return f"({left}{right})"

    min_cost = m[1][n]
    parenthesization = build_parenthesization(1, n)

    return min_cost, parenthesization


# Example usage
if __name__ == "__main__":
    dimensions = [10, 30, 5, 60]
    cost, expression = matrix_chain_order(dimensions)
    print(f"Minimum Scalar Multiplications: {cost}")
    print(f"Optimal Parenthesization: {expression}")