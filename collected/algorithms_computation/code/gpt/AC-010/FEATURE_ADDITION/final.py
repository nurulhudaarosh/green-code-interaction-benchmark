from typing import Dict, Sequence, Tuple, Union


def matrix_chain_order(
    p: Sequence[int],
    include_operation_summary: bool = False,
) -> Union[
    Tuple[int, str],
    Dict[str, Union[int, str]]
]:
    """
    Matrix Chain Planner.

    Given dimensions p0..pn:
        A1 = p0 x p1
        A2 = p1 x p2
        ...
        An = p(n-1) x pn

    Finds:
        - minimum scalar multiplication cost
        - deterministic optimal parenthesization

    Tie-breaking:
        If multiple splits produce the same minimum cost, choose the
        smallest split index.

    Optional feature:
        If include_operation_summary=True, return an additional field
        containing the deterministic number of candidate split evaluations.

    Returns:
        Feature disabled:
            (cost, parenthesization)

        Feature enabled:
            {
                "cost": cost,
                "parenthesization": parenthesization,
                "operation_summary": operation_count
            }
    """

    if len(p) < 2:
        raise ValueError("p must contain at least two dimensions")

    if any(not isinstance(x, int) or isinstance(x, bool) or x <= 0 for x in p):
        raise ValueError("all matrix dimensions must be positive integers")

    n = len(p) - 1

    # Original behavior for a chain containing one matrix.
    if n == 1:
        cost = 0
        parenthesization = "A1"
        operation_count = 0

        if include_operation_summary:
            return {
                "cost": cost,
                "parenthesization": parenthesization,
                "operation_summary": operation_count,
            }

        return cost, parenthesization

    # dp[i][j] = minimum multiplication cost for Ai ... Aj
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    # split[i][j] = optimal split k for Ai ... Aj
    split = [[0] * (n + 1) for _ in range(n + 1)]

    # Deterministic count of candidate split evaluations.
    operation_count = 0

    # Interval DP: process shorter chains before longer chains.
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1

            best_cost = None
            best_k = None

            # Try split indices from smallest to largest.
            for k in range(i, j):
                operation_count += 1

                cost = (
                    dp[i][k]
                    + dp[k + 1][j]
                    + p[i - 1] * p[k] * p[j]
                )

                # Strictly smaller only.
                # Equal costs do not replace the existing choice, so
                # the smallest k is deterministically preserved.
                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    best_k = k

            dp[i][j] = best_cost
            split[i][j] = best_k

    def build_parenthesization(i: int, j: int) -> str:
        if i == j:
            return f"A{i}"

        k = split[i][j]

        left = build_parenthesization(i, k)
        right = build_parenthesization(k + 1, j)

        return f"({left}{right})"

    minimum_cost = dp[1][n]
    parenthesization = build_parenthesization(1, n)

    # Preserve every original output and behavior when the feature
    # is disabled or not requested.
    if not include_operation_summary:
        return minimum_cost, parenthesization

    return {
        "cost": minimum_cost,
        "parenthesization": parenthesization,
        "operation_summary": operation_count,
    }


# Tests
if __name__ == "__main__":
    dimensions = [40, 20, 30, 10, 30]

    # Original behavior: unchanged two-field result.
    result_without_summary = matrix_chain_order(dimensions)
    print("Without summary:")
    print(result_without_summary)
    # Expected:
    # (26000, '((A1(A2A3))A4)')

    # New feature enabled.
    result_with_summary = matrix_chain_order(
        dimensions,
        include_operation_summary=True,
    )
    print("\nWith summary:")
    print(result_with_summary)
    # Expected:
    # {
    #     'cost': 26000,
    #     'parenthesization': '((A1(A2A3))A4)',
    #     'operation_summary': 10
    # }

    # Smallest valid non-empty chain.
    assert matrix_chain_order([5, 10]) == (0, "A1")

    one_matrix_with_summary = matrix_chain_order(
        [5, 10],
        include_operation_summary=True,
    )
    assert one_matrix_with_summary == {
        "cost": 0,
        "parenthesization": "A1",
        "operation_summary": 0,
    }

    # Original known example.
    assert matrix_chain_order([40, 20, 30, 10, 30]) == (
        26000,
        "((A1(A2A3))A4)",
    )

    print("\nAll tests passed.")