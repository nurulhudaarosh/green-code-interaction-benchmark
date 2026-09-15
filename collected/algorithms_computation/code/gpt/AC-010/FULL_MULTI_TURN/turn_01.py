def matrix_chain_planner(p):
    """
    Find the minimum scalar multiplication cost and an optimal
    parenthesization for a matrix chain.

    Input:
        p: list of dimensions [p0, p1, ..., pn]

    Output:
        {
            "cost": minimum scalar multiplication cost,
            "parenthesization": optimal parenthesization
        }

    Tie-breaking:
        For equal costs, choose the smallest split index k.
    """

    # Validate input
    if not isinstance(p, list):
        raise TypeError("p must be a list")

    if len(p) < 2:
        raise ValueError("p must contain at least two dimensions")

    if any(not isinstance(x, int) or isinstance(x, bool) or x <= 0 for x in p):
        raise ValueError("All dimensions must be positive integers")

    # Number of matrices
    n = len(p) - 1

    # dp[i][j] = minimum cost for Ai...Aj
    # Matrices are numbered from 1 to n.
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    # split[i][j] = split index k giving the optimal solution
    split = [[0] * (n + 1) for _ in range(n + 1)]

    # Chain lengths from 2 matrices up to n matrices
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1

            best_cost = float("inf")
            best_k = None

            # Process k in increasing order.
            # Therefore, the first minimum automatically gives
            # the smallest split index in case of a tie.
            for k in range(i, j):
                cost = (
                    dp[i][k]
                    + dp[k + 1][j]
                    + p[i - 1] * p[k] * p[j]
                )

                if cost < best_cost:
                    best_cost = cost
                    best_k = k

            dp[i][j] = best_cost
            split[i][j] = best_k

    # Build the parenthesization recursively
    def build_parenthesization(i, j):
        if i == j:
            return f"A{i}"

        k = split[i][j]

        left = build_parenthesization(i, k)
        right = build_parenthesization(k + 1, j)

        return f"({left} × {right})"

    return {
        "cost": dp[1][n],
        "parenthesization": build_parenthesization(1, n)
    }


# ---------------------------------------------------------
# Examples / tests
# ---------------------------------------------------------

# Example 1
result = matrix_chain_planner([10, 20, 30])
print(result)
# {'cost': 6000, 'parenthesization': '(A1 × A2)'}


# Example 2
result = matrix_chain_planner([40, 20, 30, 10, 30])
print(result)
# Minimum cost = 26000


# Example 3: classic matrix-chain example
result = matrix_chain_planner([30, 35, 15, 5, 10, 20, 25])
print(result)
# Minimum cost = 15125


# Example 4: deterministic tie handling
# Both possible parenthesizations have the same cost.
result = matrix_chain_planner([2, 2, 2, 2])
print(result)
# {'cost': 16, 'parenthesization': '((A1 × A2) × A3)'}
# The first/smallest split k is selected when costs tie.