def matrix_chain_order(p):
    """
    p: list of matrix dimensions, length n+1, matrix i (1..n) has shape p[i-1] x p[i]
    Returns: (min_cost, parenthesization_string)
    """
    n = len(p) - 1
    if n < 1:
        raise ValueError("Need at least one matrix (p must have length >= 2)")
    if n == 1:
        return 0, "A1"

    INF = float('inf')
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    split = [[0] * (n + 1) for _ in range(n + 1)]

    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1
            best_cost = INF
            best_k = i
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + p[i - 1] * p[k] * p[j]
                if cost < best_cost:
                    best_cost = cost
                    best_k = k
            dp[i][j] = best_cost
            split[i][j] = best_k

    def build(i, j):
        if i == j:
            return f"A{i}"
        k = split[i][j]
        return f"({build(i, k)}{build(k + 1, j)})"

    return dp[n][n], build(1, n)


if __name__ == "__main__":
    p = [30, 35, 15, 5, 10, 20, 25]
    cost, parens = matrix_chain_order(p)
    print("Minimum cost:", cost)
    print("Parenthesization:", parens)