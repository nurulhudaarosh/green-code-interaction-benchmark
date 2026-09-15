def matrix_chain_order(p: list[int]) -> tuple[int, str]:
    """
    Computes the minimum scalar multiplication cost and optimal parenthesization
    for a chain of matrices with dimensions p = [p0, p1, ..., pn].
    
    Tie-breaking rule: Strictly prefers the smallest split index k upon equal costs.
    """
    n = len(p) - 1
    if n <= 0:
        return 0, ""
    if n == 1:
        return 0, "A1"

    # m[i][j]: minimum cost to multiply A_i...A_j (1-indexed)
    # s[i][j]: optimal split index k for subchain A_i...A_j
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    # L is the chain length (from 2 up to n)
    for L in range(2, n + 1):
        for i in range(1, n - L + 2):
            j = i + L - 1
            m[i][j] = float('inf')
            
            # Iterate split index k in strictly ascending order: i <= k < j
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                
                # Strict '<' guarantees that if cost == m[i][j], 
                # the smaller index k already stored in s[i][j] is maintained.
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    def build_expression(i: int, j: int) -> str:
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left_expr = build_expression(i, k)
        right_expr = build_expression(k + 1, j)
        return f"({left_expr}{right_expr})"

    min_cost = m[1][n]
    optimal_parenthesization = build_expression(1, n)

    return min_cost, optimal_parenthesization


# Demonstration of deterministic tie-handling
if __name__ == "__main__":
    # 3 identical matrices (10x10): k=1 and k=2 both cost 2000.
    dims = [10, 10, 10, 10]
    cost, parenthesization = matrix_chain_order(dims)
    
    print(f"Dimensions: {dims}")
    print(f"Minimum Scalar Multiplications: {cost}")
    print(f"Optimal Parenthesization: {parenthesization}")
    # Expected Output: (A1(A2A3)) due to choosing k=1 over k=2