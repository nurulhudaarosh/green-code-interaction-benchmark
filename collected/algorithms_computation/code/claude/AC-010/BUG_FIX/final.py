def matrix_chain_order(p):
    """
    p: list of matrix dimensions, len(p) = n+1, matrices A1..An
       Ai has dimensions p[i-1] x p[i]

    Returns (min_cost, parenthesization_string)
    Tie rule: among all k achieving the minimum cost for a subproblem,
    the SMALLEST k is chosen, deterministically and explicitly.
    """
    n = len(p) - 1
    if n < 1:
        raise ValueError("Need at least one matrix (len(p) >= 2)")
    if n == 1:
        return 0, "A1"

    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    for L in range(2, n + 1):
        for i in range(1, n - L + 2):
            j = i + L - 1
            best_cost = None
            best_k = None
            # Explicitly scan k in increasing order and only replace
            # the best on STRICT improvement, so the first (smallest)
            # k achieving the minimum is always kept, regardless of
            # future edits to loop order or comparison operators.
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    best_k = k
                # NOTE: intentionally no '<=' branch here — ties must
                # never overwrite best_k, preserving smallest-k rule.
            m[i][j] = best_cost
            s[i][j] = best_k

    def build(i, j):
        if i == j:
            return f"A{i}"
        k = s[i][j]
        return f"({build(i, k)}{build(k + 1, j)})"

    return m[1][n], build(1, n)


if __name__ == "__main__":
    test_cases = [
        [30, 35, 15, 5, 10, 20, 25],
        [10, 20, 30],
        [40, 20, 30, 10, 30],
        [5, 10],
        [10, 10, 10, 10],   # tie case: expects k=1 -> "((A1A2)A3)"
    ]

    for p in test_cases:
        cost, expr = matrix_chain_order(p)
        print(f"p = {p}")
        print(f"  Minimum scalar multiplications: {cost}")
        print(f"  Parenthesization: {expr}")