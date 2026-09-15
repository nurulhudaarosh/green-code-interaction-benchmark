from typing import List, Dict, Union


def matrix_chain_order(p: List[int]) -> Dict[str, Union[int, str]]:
    """
    Find the minimum scalar multiplication cost and optimal
    parenthesization for a matrix chain.

    Given p = [p0, p1, ..., pn], there are n matrices:
        A1: p0 x p1
        A2: p1 x p2
        ...
        An: p(n-1) x pn

    Tie-breaking:
        If multiple splits produce the same minimum cost,
        the smallest split index k is selected.

    Returns:
        {
            "min_cost": minimum scalar multiplication cost,
            "parenthesization": optimal parenthesization
        }
    """

    # Validate input.
    if not isinstance(p, list):
        raise TypeError("p must be a list of positive integers.")

    if len(p) < 2:
        raise ValueError("p must contain at least two dimensions.")

    if any(not isinstance(x, int) or isinstance(x, bool) or x <= 0 for x in p):
        raise ValueError("All matrix dimensions must be positive integers.")

    # Number of matrices.
    n = len(p) - 1

    # dp[i][j] = minimum cost for Ai...Aj.
    # We use 1-based matrix indices.
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    # split[i][j] = split index k that gives the optimal
    # parenthesization for Ai...Aj.
    split = [[0] * (n + 1) for _ in range(n + 1)]

    # Interval DP.
    #
    # length is the number of matrices in the interval.
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1

            best_cost = float("inf")
            best_k = None

            # Try every possible split.
            # Iterating k from smallest to largest naturally
            # enforces the required tie-breaking rule.
            for k in range(i, j):
                cost = (
                    dp[i][k]
                    + dp[k + 1][j]
                    + p[i - 1] * p[k] * p[j]
                )

                if cost < best_cost:
                    best_cost = cost
                    best_k = k

                # On equal cost, do nothing because k is being
                # considered from smallest to largest.
                # Therefore the first minimum is the smallest k.

            dp[i][j] = best_cost
            split[i][j] = best_k

    # Reconstruct the parenthesization.
    def build_parenthesization(i: int, j: int) -> str:
        if i == j:
            return f"A{i}"

        k = split[i][j]

        left = build_parenthesization(i, k)
        right = build_parenthesization(k + 1, j)

        return f"({left}{right})"

    return {
        "min_cost": dp[1][n],
        "parenthesization": build_parenthesization(1, n),
    }


# Example usage
if __name__ == "__main__":
    dimensions = [10, 20, 30, 40, 30]

    result = matrix_chain_order(dimensions)

    print(result)