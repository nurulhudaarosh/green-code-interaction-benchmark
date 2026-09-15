def matrix_chain_order(p):
    """
    p: list of matrix dimensions, len(p) = n+1, matrices A1..An
       Ai has dimensions p[i-1] x p[i]

    Returns (min_cost, parenthesization_string)
    """
    n = len(p) - 1
    if n < 1:
        raise ValueError("Need at least one matrix (len(p) >= 2)")
    if n == 1:
        return 0, "A1"

    # m[i][j]: min cost to compute product Ai..Aj (1-indexed)
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    for L in range(2, n + 1):          # chain length
        for i in range(1, n - L + 2):
            j = i + L - 1
            m[i][j] = float('inf')
            for k in range(i, j):      # split point, deterministic order -> smallest k wins ties
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    def build(i, j):
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = build(i, k)
        right = build(k + 1, j)
        return f"({left}{right})"

    return m[1][n], build(1, n)


if __name__ == "__main__":
    # Deterministic demo cases (no input(), no randomness)
    test_cases = [
        [30, 35, 15, 5, 10, 20, 25],
        [10, 20, 30],
        [40, 20, 30, 10, 30],
        [5, 10],
    ]

    for p in test_cases:
        cost, expr = matrix_chain_order(p)
        print(f"p = {p}")
        print(f"  Minimum scalar multiplications: {cost}")
        print(f"  Parenthesization: {expr}")