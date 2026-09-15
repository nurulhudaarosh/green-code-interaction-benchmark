from typing import List, Dict, Union


def matrix_chain_order(p: List[int]) -> Dict[str, Union[int, str]]:
    """
    Matrix Chain Planner.

    Given p = [p0, p1, ..., pn], there are n matrices:
        A1: p0 x p1
        A2: p1 x p2
        ...
        An: p(n-1) x pn

    Returns:
        {
            "min_cost": minimum scalar multiplication cost,
            "parenthesization": optimal parenthesization
        }

    Tie-breaking:
        If multiple splits have the same minimum cost,
        choose the smallest split index k.
    """

    # Input validation
    if not isinstance(p, list):
        raise TypeError("p must be a list of positive integers.")

    if len(p) < 2:
        raise ValueError("p must contain at least two dimensions.")

    if any(
        not isinstance(x, int) or isinstance(x, bool) or x <= 0
        for x in p
    ):
        raise ValueError("All matrix dimensions must be positive integers.")

    n = len(p) - 1

    # dp[i][j] = minimum cost for Ai...Aj
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    # split[i][j] = optimal split index k
    split = [[0] * (n + 1) for _ in range(n + 1)]

    # Interval dynamic programming
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1

            best_cost = float("inf")
            best_k = None

            # k is intentionally examined from smallest to largest.
            # Therefore, if costs are equal, the first minimum
            # automatically has the smallest split index.
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

    # Reconstruct optimal parenthesization.
    def build(i: int, j: int) -> str:
        if i == j:
            return f"A{i}"

        k = split[i][j]

        left = build(i, k)
        right = build(k + 1, j)

        return f"({left}{right})"

    return {
        "min_cost": dp[1][n],
        "parenthesization": build(1, n),
    }


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def test_repeated_values():
    """
    Repeated dimensions are valid.

    p = [10, 10, 10, 10]
    All matrices are 10 x 10.

    Both possible parenthesizations have the same cost:
        (A1A2)A3
        A1(A2A3)

    The valid tie-breaking rule chooses the smallest split,
    k = 1, giving:
        ((A1A2)A3)
    """

    result = matrix_chain_order([10, 10, 10, 10])

    assert result == {
        "min_cost": 2000,
        "parenthesization": "((A1A2)A3)",
    }


def test_repeated_values_with_optimal_choice():
    """
    Repeated dimensions can occur in only some positions.

    The algorithm must still use the matrix indices and
    dimensions exactly as supplied.
    """

    result = matrix_chain_order([5, 10, 5, 10, 5])

    assert result["min_cost"] == 375
    assert result["parenthesization"] == "(((A1A2)A3)A4)"


def test_deterministic_tie():
    """
    For [10, 10, 10, 10], both possible splits for
    the full chain can have equal cost.

    The smallest split index must be selected.
    """

    result1 = matrix_chain_order([10, 10, 10, 10])
    result2 = matrix_chain_order([10, 10, 10, 10])

    # Same input must always produce exactly the same result.
    assert result1 == result2

    # Smallest split k = 1 is selected.
    assert result1["parenthesization"] == "((A1A2)A3)"


def test_single_matrix():
    """
    Smallest valid input: two dimensions represent one matrix.

    No multiplication is necessary.
    """

    result = matrix_chain_order([5, 10])

    assert result == {
        "min_cost": 0,
        "parenthesization": "A1",
    }


def test_standard_example():
    """
    Standard matrix-chain example.
    """

    result = matrix_chain_order([10, 20, 30, 40, 30])

    assert result == {
        "min_cost": 30000,
        "parenthesization": "(((A1A2)A3)A4)",
    }


def test_repeated_dimension_values_do_not_change_indices():
    """
    Repeated values must not cause matrices to be merged or
    treated as identical.
    """

    p = [2, 3, 3, 2]

    result = matrix_chain_order(p)

    # A1 = 2x3
    # A2 = 3x3
    # A3 = 3x2
    #
    # (A1A2)A3:
    # 2*3*3 + 2*3*2 = 18 + 12 = 30
    #
    # A1(A2A3):
    # 3*3*2 + 2*3*2 = 18 + 12 = 30
    #
    # Equal cost -> smallest split k=1.
    assert result == {
        "min_cost": 30,
        "parenthesization": "((A1A2)A3)",
    }


def run_tests():
    test_repeated_values()
    test_repeated_values_with_optimal_choice()
    test_deterministic_tie()
    test_single_matrix()
    test_standard_example()
    test_repeated_dimension_values_do_not_change_indices()

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()