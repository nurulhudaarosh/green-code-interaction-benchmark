"""
Problem: Matrix Chain Multiplication

Given dimensions p0, p1, ..., pn describing n matrices A1..An where
Ai has dimensions p[i-1] x p[i], find the minimum number of scalar
multiplications needed to compute the product A1*A2*...*An, along
with an optimal parenthesization.

Key constraints:
- len(p) = n + 1 for n matrices (n >= 1).
- All dimensions are positive integers.
- Matrix multiplication is associative but not commutative, so the
  order of multiplication (parenthesization) affects total cost but
  not the final matrix result.
- Ties: when multiple split points k give the same minimum cost for
  a subproblem (i, j), choose the smallest split index k.

Required output:
- The minimum total scalar multiplication cost.
- A string showing an optimal parenthesization (matrices labeled
  A1, A2, ..., An).

Algorithm (interval DP over matrix-chain ranges):
- Let m[i][j] = minimum cost to compute the product Ai*A(i+1)*...*Aj.
- Base case: m[i][i] = 0 (single matrix, no multiplication needed).
- Recurrence, for i < j:
    m[i][j] = min over k in [i, j-1] of
              m[i][k] + m[k+1][j] + p[i-1]*p[k]*p[j]
  Track the best k (s[i][j]) that achieves this minimum, breaking
  ties by preferring the smallest k.
- Fill the table by increasing chain length L = j - i + 1, from
  L = 2 up to L = n, so that subproblems are solved before the
  problems that depend on them.
- The answer is m[1][n]; the parenthesization is reconstructed
  recursively from the split table s[i][j].

This is a deterministic O(n^3) time, O(n^2) space DP with no
randomness, network access, or external dependencies.
"""

from typing import List, Tuple


def matrix_chain_order(p: List[int]) -> Tuple[int, List[List[int]]]:
    """
    Compute the minimum scalar multiplication cost for the matrix
    chain with dimension list p (len(p) = n + 1), and the split
    table used to reconstruct an optimal parenthesization.

    Returns:
        (min_cost, s) where:
        - min_cost is the minimum number of scalar multiplications.
        - s is a 1-indexed (size (n+1) x (n+1)) table where
          s[i][j] is the chosen split point k for subchain (i, j),
          meaning the optimal split is (Ai..Ak)(A(k+1)..Aj).
    """
    n = len(p) - 1  # number of matrices
    if n < 1:
        raise ValueError("Need at least one matrix (len(p) >= 2).")
    if n == 1:
        return 0, [[0] * (n + 1) for _ in range(n + 1)]

    # m[i][j]: min cost for chain Ai..Aj (1-indexed, i,j in [1..n])
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    for length in range(2, n + 1):          # chain length
        for i in range(1, n - length + 2):  # start index
            j = i + length - 1              # end index
            m[i][j] = float('inf')
            for k in range(i, j):
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                # Strict '<' preserves the smallest k on ties,
                # since k increases in this loop.
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    return m[1][n], s


def build_parenthesization(s: List[List[int]], i: int, j: int) -> str:
    """Recursively reconstruct an optimal parenthesization string."""
    if i == j:
        return f"A{i}"
    k = s[i][j]
    left = build_parenthesization(s, i, k)
    right = build_parenthesization(s, k + 1, j)
    return f"({left}{right})"


def solve(p: List[int]) -> Tuple[int, str]:
    """
    Solve the matrix chain multiplication problem.

    Args:
        p: dimension list [p0, p1, ..., pn] for n matrices,
           where Ai has shape p[i-1] x p[i].

    Returns:
        (min_cost, parenthesization_string)
    """
    n = len(p) - 1
    min_cost, s = matrix_chain_order(p)
    if n == 1:
        return 0, "A1"
    parenthesization = build_parenthesization(s, 1, n)
    return min_cost, parenthesization


if __name__ == "__main__":
    # Example: dimensions for matrices A1(30x35), A2(35x15), A3(15x5),
    # A4(5x10), A5(10x20), A6(20x25)
    p = [30, 35, 15, 5, 10, 20, 25]
    cost, order = solve(p)
    print(f"Dimensions p: {p}")
    print(f"Minimum scalar multiplications: {cost}")
    print(f"Optimal parenthesization: {order}")

    # A few extra deterministic test cases
    for test_p in ([10, 20], [40, 20, 30, 10, 30], [1, 2, 3, 4]):
        c, o = solve(test_p)
        print(f"\nDimensions p: {test_p}")
        print(f"Minimum scalar multiplications: {c}")
        print(f"Optimal parenthesization: {o}")