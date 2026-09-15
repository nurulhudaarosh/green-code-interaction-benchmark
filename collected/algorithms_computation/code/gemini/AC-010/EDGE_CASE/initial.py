def matrix_chain_order(p: list[int]) -> tuple[int, str]:
    """
    Computes the minimum scalar multiplication cost and parenthesization 
    for a chain of matrices defined by dimensions p.
    """
    n = len(p) - 1
    if n <= 0:
        return 0, ""
    if n == 1:
        return 0, "A1"

    # m[i][j] stores the minimum multiplication cost for A_i..A_j
    # s[i][j] stores the optimal split point k
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    # L is the chain length
    for L in range(2, n + 1):
        for i in range(1, n - L + 2):
            j = i + L - 1
            m[i][j] = float('inf')
            
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                
                # Use strictly less (<) to prefer the smallest split index k on equal cost
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    def build_parenthesis(i: int, j: int) -> str:
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = build_parenthesis(i, k)
        right = build_parenthesis(k + 1, j)
        return f"({left}{right})"

    min_cost = m[1][n]
    parenthesization = build_parenthesis(1, n)
    return min_cost, parenthesization


# Example Usage
if __name__ == "__main__":
    dimensions = [40, 20, 30, 10, 30]
    cost, structure = matrix_chain_order(dimensions)
    print(f"Minimum Cost: {cost}")
    print(f"Optimal Structure: {structure}")