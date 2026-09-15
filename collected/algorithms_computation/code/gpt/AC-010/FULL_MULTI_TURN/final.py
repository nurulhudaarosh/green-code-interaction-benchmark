def matrix_chain_planner(p, include_operation_summary=False):
    """
    Matrix Chain Planner.

    Given p = [p0, p1, ..., pn], there are n matrices:
        A1: p0 x p1
        A2: p1 x p2
        ...
        An: p(n-1) x pn

    Returns:
        {
            "cost": minimum scalar multiplication cost,
            "parenthesization": optimal parenthesization
        }

    If include_operation_summary=True, also returns:
        "operation_summary": number of split candidates evaluated

    Tie-breaking:
        Equal-cost choices always use the smallest split index k.
    """

    # -------------------------
    # Input validation
    # -------------------------
    if not isinstance(p, list):
        raise TypeError("p must be a list")

    if len(p) < 2:
        raise ValueError("p must contain at least two dimensions")

    if any(
        not isinstance(x, int) or isinstance(x, bool) or x <= 0
        for x in p
    ):
        raise ValueError("All dimensions must be positive integers")

    if not isinstance(include_operation_summary, bool):
        raise TypeError("include_operation_summary must be a boolean")

    n = len(p) - 1

    # dp[i][j] = minimum cost for Ai ... Aj
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    # split[i][j] = optimal split index
    split = [[0] * (n + 1) for _ in range(n + 1)]

    operation_count = 0

    # -------------------------
    # Interval Dynamic Programming
    # -------------------------
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1

            best_cost = float("inf")
            best_k = None

            # IMPORTANT:
            # k is examined from smallest to largest.
            # Strict '<' means an equal-cost later k
            # cannot replace the smaller k.
            for k in range(i, j):
                operation_count += 1

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

    # -------------------------
    # Construct parenthesization
    # -------------------------
    def build_parenthesization(i, j):
        if i == j:
            return f"A{i}"

        k = split[i][j]

        left = build_parenthesization(i, k)
        right = build_parenthesization(k + 1, j)

        return f"({left} × {right})"

    result = {
        "cost": dp[1][n],
        "parenthesization": build_parenthesization(1, n)
    }

    # Preserve optional operation_summary behavior.
    if include_operation_summary:
        result["operation_summary"] = operation_count

    return result


# =========================================================
# TESTS
# =========================================================

# ---------------------------------------------------------
# Test 1: Smallest valid input
# ---------------------------------------------------------
assert matrix_chain_planner([5, 10]) == {
    "cost": 0,
    "parenthesization": "A1"
}


# ---------------------------------------------------------
# Test 2: Basic two-matrix case
# ---------------------------------------------------------
assert matrix_chain_planner([10, 20, 30]) == {
    "cost": 6000,
    "parenthesization": "(A1 × A2)"
}


# ---------------------------------------------------------
# Test 3: Repeated dimensions
# ---------------------------------------------------------
# All matrices are 2 x 2.
# Repeated values must be handled normally.
assert matrix_chain_planner([2, 2, 2, 2]) == {
    "cost": 16,
    "parenthesization": "((A1 × A2) × A3)"
}


# ---------------------------------------------------------
# Test 4: Deterministic tie
# ---------------------------------------------------------
# For [2, 2, 2, 2]:
#
# k = 1:
#   (A1) x (A2 x A3)
#   cost = 8 + 8 = 16
#
# k = 2:
#   (A1 x A2) x (A3)
#   cost = 8 + 8 = 16
#
# Both have the same cost.
# Required rule: choose smallest k = 1.
#
# Therefore the expected result is deterministic.
result = matrix_chain_planner([2, 2, 2, 2])

assert result["cost"] == 16
assert result["parenthesization"] == "((A1 × A2) × A3)"


# ---------------------------------------------------------
# Test 5: Repeated values with more matrices
# ---------------------------------------------------------
# Every dimension is identical.
# There are many equal-cost parenthesizations.
# The smallest split must consistently be selected.
result = matrix_chain_planner([3, 3, 3, 3, 3])

assert result["cost"] == 81
assert result["parenthesization"] == "(((A1 × A2) × A3) × A4)"


# ---------------------------------------------------------
# Test 6: Deterministic tie + operation summary
# ---------------------------------------------------------
result = matrix_chain_planner(
    [2, 2, 2, 2],
    include_operation_summary=True
)

assert result == {
    "cost": 16,
    "parenthesization": "((A1 × A2) × A3)",
    "operation_summary": 3
}


# ---------------------------------------------------------
# Test 7: Repeated dimensions + operation summary
# ---------------------------------------------------------
# Four matrices:
# length 2 -> 3 split decisions
# length 3 -> 2 split decisions
# length 4 -> 1 split decision
# total = 6
result = matrix_chain_planner(
    [5, 5, 5, 5, 5],
    include_operation_summary=True
)

assert result["cost"] == 375
assert result["parenthesization"] == "(((A1 × A2) × A3) × A4)"
assert result["operation_summary"] == 6


# ---------------------------------------------------------
# Test 8: Classic matrix-chain example
# ---------------------------------------------------------
assert matrix_chain_planner(
    [30, 35, 15, 5, 10, 20, 25]
) == {
    "cost": 15125,
    "parenthesization":
        "((A1 × (A2 × A3)) × ((A4 × A5) × A6))"
}


# ---------------------------------------------------------
# Test 9: Feature disabled preserves original output
# ---------------------------------------------------------
result = matrix_chain_planner([2, 2, 2, 2])

assert list(result.keys()) == [
    "cost",
    "parenthesization"
]

assert "operation_summary" not in result


# ---------------------------------------------------------
# Test 10: Invalid input
# ---------------------------------------------------------
try:
    matrix_chain_planner([10])
    assert False
except ValueError:
    pass


# ---------------------------------------------------------
# Test 11: Invalid repeated-value input
# ---------------------------------------------------------
try:
    matrix_chain_planner([10, 0, 10])
    assert False
except ValueError:
    pass


# ---------------------------------------------------------
# Test 12: Non-list input
# ---------------------------------------------------------
try:
    matrix_chain_planner((10, 20, 30))
    assert False
except TypeError:
    pass


# ---------------------------------------------------------
# Test 13: Invalid operation-summary flag
# ---------------------------------------------------------
try:
    matrix_chain_planner([10, 20], include_operation_summary=1)
    assert False
except TypeError:
    pass


print("All tests passed.")

print(
    matrix_chain_planner(
        [2, 2, 2, 2],
        include_operation_summary=True
    )
)