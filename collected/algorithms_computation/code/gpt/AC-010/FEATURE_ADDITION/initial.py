from typing import Sequence, Tuple


def matrix_chain_order(p: Sequence[int]) -> Tuple[int, str]:
    """
    Find the minimum scalar multiplication cost and deterministic
    parenthesization for a matrix chain.

    Given p = [p0, p1, ..., pn]:
        A1 = p0 x p1
        A2 = p1 x p2
        ...
        An = p(n-1) x pn

    Returns:
        (minimum_cost, parenthesization)

    Tie-breaking:
        If multiple splits have the same minimum cost, the smallest
        split index k is chosen.
    """

    if len(p) < 2:
        raise ValueError("p must contain at least two dimensions")

    if any(not isinstance(x, int) or isinstance(x, bool) or x <= 0 for x in p):
        raise ValueError("all matrix dimensions must be positive integers")

    n = len(p) - 1

    # One matrix requires no multiplication.
    if n == 1:
        return 0, "A1"

    # dp[i][j] = minimum cost for Ai ... Aj
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    # split[i][j] = split position k producing the optimal cost
    split = [[0] * (n + 1) for _ in range(n + 1)]

    # Build intervals from shorter to longer.
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1

            best_cost = None
            best_k = None

            # k increases from i to j-1.
            # Therefore, on equal cost, the first one is the
            # smallest split index.
            for k in range(i, j):
                cost = (
                    dp[i][k]
                    + dp[k + 1][j]
                    + p[i - 1] * p[k] * p[j]
                )

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

    return dp[1][n], build_parenthesization(1, n)


# Example
if __name__ == "__main__":
    dimensions = [40, 20, 30, 10, 30]

    cost, parenthesization = matrix_chain_order(dimensions)

    print("Minimum cost:", cost)
    print("Parenthesization:", parenthesization)