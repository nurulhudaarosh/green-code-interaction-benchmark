def matrix_chain_planner(p):
    """
    Matrix Chain Planner.

    Given matrix dimensions p = [p0, p1, ..., pn], find:
      1. Minimum scalar multiplication cost.
      2. An optimal parenthesization.

    Tie-breaking:
      If multiple split points have the same minimum cost,
      choose the smallest split index k.

    Returns exactly:
        {
            "cost": minimum_scalar_multiplication_cost,
            "parenthesization": optimal_parenthesization
        }
    """

    # Input validation
    if not isinstance(p, list):
        raise TypeError("p must be a list")

    if len(p) < 2:
        raise ValueError("p must contain at least two dimensions")

    if any(
        not isinstance(x, int) or isinstance(x, bool) or x <= 0
        for x in p
    ):
        raise ValueError("All dimensions must be positive integers")

    # Number of matrices
    n = len(p) - 1

    # dp[i][j] = minimum cost for multiplying Ai ... Aj
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    # split[i][j] = split index k used for the optimal solution
    split = [[0] * (n + 1) for _ in range(n + 1)]

    # Interval dynamic programming over all matrix-chain ranges
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1

            best_cost = float("inf")
            best_k = None

            # Process k from smallest to largest.
            # Using strict '<' keeps the smallest k when costs tie.
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

    # Construct the optimal parenthesization
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
# Tests
# ---------------------------------------------------------

# One matrix: no multiplication required.
assert matrix_chain_planner([5, 10]) == {
    "cost": 0,
    "parenthesization": "A1"
}

# Two matrices.
assert matrix_chain_planner([10, 20, 30]) == {
    "cost": 6000,
    "parenthesization": "(A1 × A2)"
}

# Tie case:
# k=1 and k=2 both have cost 16.
# Smallest split k=1 must be selected.
assert matrix_chain_planner([2, 2, 2, 2]) == {
    "cost": 16,
    "parenthesization": "((A1 × A2) × A3)"
}

# Classic matrix-chain example.
assert matrix_chain_planner([30, 35, 15, 5, 10, 20, 25]) == {
    "cost": 15125,
    "parenthesization": "((A1 × (A2 × A3)) × ((A4 × A5) × A6))"
}

# Invalid input tests.
try:
    matrix_chain_planner([10])
    assert False
except ValueError:
    pass

try:
    matrix_chain_planner([10, 0, 20])
    assert False
except ValueError:
    pass

try:
    matrix_chain_planner([10, -5, 20])
    assert False
except ValueError:
    pass

try:
    matrix_chain_planner("10,20,30")
    assert False
except TypeError:
    pass

print("All tests passed.")
print(matrix_chain_planner([2, 2, 2, 2]))