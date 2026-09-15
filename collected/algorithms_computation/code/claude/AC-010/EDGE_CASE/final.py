"""
Matrix Chain Planner - Minimum Scalar Multiplication Cost

Restated problem:
    Given matrix dimensions p0, p1, ..., pn describing n matrices
    A1..An, where matrix Ai has shape p[i-1] x p[i], find:
      1. The minimum total number of scalar multiplications needed to
         compute the product A1 * A2 * ... * An (order of multiplication
         does not change the result, only the cost).
      2. An optimal parenthesization achieving that minimum cost.

Key constraints:
    - len(p) == n + 1 for n matrices; n >= 1.
    - All dimensions p[i] must be positive integers.
    - Consecutive matrices are guaranteed conformable by construction
      (Ai has shape p[i-1] x p[i], A(i+1) has shape p[i] x p[i+1]).
    - Difficult/edge cases explicitly handled:
        * Repeated values in p (e.g. many equal dimensions, including
          all dimensions equal, or repeated non-adjacent values) must
          not break correctness or determinism.
        * Ties: when multiple split points k for a given (i, j) achieve
          the same minimum cost, the SMALLEST split index k must always
          be chosen. This must hold deterministically regardless of
          value repetition, and must be preserved across repeated runs.

Required output:
    - min_cost: the minimum number of scalar multiplications (m[1][n]).
    - A fully parenthesized expression string, e.g. "((A1 A2) (A3 A4))",
      built using the deterministic (smallest-k) split choices.

Algorithm (interval DP over matrix-chain ranges):
    Let m[i][j] = minimum cost to compute the product Ai * A(i+1) * ... * Aj.
    Base case: m[i][i] = 0 (single matrix, no multiplication needed).
    Recurrence, for i < j:
        m[i][j] = min over k in [i, j-1] of:
            m[i][k] + m[k+1][j] + p[i-1] * p[k] * p[j]
    Fill the table by increasing chain length L = j - i + 1, from 2..n.
    For each (i, j), scan split points k in increasing order and only
    update the best cost on a STRICT improvement (cost < current best).
    This guarantees that on ties (cost == current best), the earlier
    (smaller) k already recorded is kept -- deterministic tie-breaking,
    independent of repeated dimension values.
    Time complexity: O(n^3). Space complexity: O(n^2).
"""

from typing import List, Tuple


def matrix_chain_order(p: List[int]) -> Tuple[int, List[List[int]]]:
    """Compute minimum cost table m and split table s for matrix chain
    multiplication given dimension list p (length n+1 for n matrices).

    Returns:
        (min_cost, s) where min_cost is m[1][n] and s is the split table
        (1-indexed, s[i][j] valid for i < j).
    """
    if len(p) < 2:
        raise ValueError("p must have at least 2 dimensions (>=1 matrix).")
    for d in p:
        if not isinstance(d, int) or d <= 0:
            raise ValueError("All dimensions in p must be positive integers.")

    n = len(p) - 1  # number of matrices

    # 1-indexed tables of size (n+1) x (n+1); index 0 unused.
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    # L = chain length (number of matrices in the subchain)
    for L in range(2, n + 1):
        for i in range(1, n - L + 2):
            j = i + L - 1
            m[i][j] = float("inf")
            best_k = i
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                if cost < m[i][j]:
                    # Strict improvement only: on ties, the earlier
                    # (smaller) k found first is retained, giving
                    # deterministic smallest-split-index tie-breaking
                    # even when dimensions repeat and produce equal costs.
                    m[i][j] = cost
                    best_k = k
            s[i][j] = best_k

    return m[1][n], s


def build_parenthesization(s: List[List[int]], i: int, j: int) -> str:
    """Recursively reconstruct the optimal parenthesization as a string
    using matrix labels A{i}..A{j}."""
    if i == j:
        return f"A{i}"
    k = s[i][j]
    left = build_parenthesization(s, i, k)
    right = build_parenthesization(s, k + 1, j)
    return f"({left} {right})"


def solve(p: List[int]) -> Tuple[int, str]:
    """Convenience wrapper: returns (min_cost, parenthesization_string)."""
    n = len(p) - 1
    if n == 1:
        return 0, "A1"
    min_cost, s = matrix_chain_order(p)
    expr = build_parenthesization(s, 1, n)
    return min_cost, expr


def _demo() -> None:
    """Deterministic demonstration with classic + repeated-value/tie cases."""
    test_cases = [
        [30, 35, 15, 5, 10, 20, 25],  # classic CLRS example -> cost 15125
        [10, 20, 30],                  # 2 matrices -> single split
        [40, 20, 30, 10, 30],          # 4 matrices
        [5],                            # degenerate: no matrices (n=0)
        [10, 10, 10, 10, 10],           # all dims equal -> many equal-cost splits
        [10, 20, 10, 20, 10, 20],       # repeated pattern, non-adjacent repeats
        [1, 1, 1, 1, 1, 1],             # trivial repeated 1's -> cost 0 everywhere
    ]

    for p in test_cases:
        n = len(p) - 1
        print(f"p = {p}  (n = {n} matrices)")
        if n <= 0:
            print("  No matrices to multiply.\n")
            continue
        cost, expr = solve(p)
        print(f"  Minimum scalar multiplications: {cost}")
        print(f"  Optimal parenthesization:       {expr}\n")


def _run_tests() -> None:
    """Explicit tests, including repeated-value and deterministic-tie cases.
    All original output and tie-breaking rules (smallest split index k on
    ties) are preserved and verified here."""

    # 1. Classic CLRS example: known optimal cost and parenthesization.
    p = [30, 35, 15, 5, 10, 20, 25]
    cost, expr = solve(p)
    assert cost == 15125, f"Expected 15125, got {cost}"
    assert expr == "((A1 (A2 A3)) ((A4 A5) A6))", f"Unexpected parenthesization: {expr}"

    # 2. Two matrices: trivial, single split, no ties possible.
    p = [10, 20, 30]
    cost, expr = solve(p)
    assert cost == 10 * 20 * 30
    assert expr == "(A1 A2)"

    # 3. Single matrix: no multiplication needed.
    p = [5, 9]
    cost, expr = solve(p)
    assert cost == 0
    assert expr == "A1"

    # 4. All dimensions equal -> every split at every level has identical
    #    cost. Tie-breaking must always choose the smallest k, which for
    #    a fully symmetric chain collapses to fully left-associated
    #    parenthesization: (((A1 A2) A3) A4) ... 
    p = [7, 7, 7, 7, 7]  # n = 4 matrices, all 7x7
    cost, expr = solve(p)
    # cost with all dims equal d: each multiply costs d^3, and total
    # number of multiplications performed is (n-1), so cost = (n-1)*d^3
    n = len(p) - 1
    d = 7
    expected_cost = (n - 1) * d ** 3
    assert cost == expected_cost, f"Expected {expected_cost}, got {cost}"
    assert expr == "(((A1 A2) A3) A4)", f"Unexpected tie-break result: {expr}"

    # 5. Repeated non-adjacent values with genuine cost ties at some
    #    subproblem: verify smallest-k determinism directly on the DP
    #    tables rather than assuming a specific global shape.
    p = [10, 20, 10, 20, 10, 20]
    cost, s = matrix_chain_order(p)
    n = len(p) - 1
    # Recompute m/s independently to confirm determinism across runs.
    cost2, s2 = matrix_chain_order(p)
    assert cost == cost2
    assert s == s2, "Split table must be identical across repeated runs."
    # For every (i, j), verify chosen split k is truly minimal cost AND
    # is the smallest index among all k achieving that minimal cost.
    m = [[0] * (n + 1) for _ in range(n + 1)]
    for L in range(2, n + 1):
        for i in range(1, n - L + 2):
            j = i + L - 1
            best_cost = None
            best_k_smallest = None
            for k in range(i, j):
                c = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                if best_cost is None or c < best_cost:
                    best_cost = c
                    best_k_smallest = k
            m[i][j] = best_cost
            assert s[i][j] == best_k_smallest, (
                f"Tie-break failure at (i={i}, j={j}): "
                f"expected smallest k={best_k_smallest}, got {s[i][j]}"
            )

    # 6. Trivial repeated 1's: every product costs 1 (1*1*1), ties
    #    everywhere; smallest-k rule -> fully left-associated result.
    p = [1, 1, 1, 1, 1, 1]
    cost, expr = solve(p)
    n = len(p) - 1
    assert cost == (n - 1) * 1, f"Expected {n - 1}, got {cost}"
    assert expr == "(((((A1 A2) A3) A4) A5) A6)", f"Unexpected: {expr}"

    # 7. Determinism across repeated calls on the same repeated-value input.
    p = [10, 10, 10, 10, 10]
    results = {solve(p) for _ in range(5)}
    assert len(results) == 1, "solve() must be deterministic across repeated calls."

    print("All tests passed.")


if __name__ == "__main__":
    _demo()
    _run_tests()