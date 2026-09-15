"""
Problem: Matrix Chain Multiplication (Matrix Chain Planner)

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

Required outputs (original, always present):
- The minimum total scalar multiplication cost.
- A string showing an optimal parenthesization (matrices labeled
  A1, A2, ..., An).

Optional feature (only when explicitly requested):
- `operation_summary`: a deterministic summary of the computation,
  reporting the number of major computational decisions/operations
  made by the algorithm (i.e. the number of (i, j, k) cost
  comparisons evaluated while filling the DP table). When the
  feature is not requested, this field is simply absent/None and
  every original field/requirement is unchanged.

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
- Each evaluation of the recurrence for a given (i, j, k) triple
  (i.e. each candidate split considered) counts as one "major
  computational decision/operation"; operation_summary reports the
  total count of these when requested.

This is a deterministic O(n^3) time, O(n^2) space DP with no
randomness, network access, or external dependencies.
"""

from typing import List, Tuple, NamedTuple, Optional


class MatrixChainResult(NamedTuple):
    min_cost: int
    parenthesization: str
    operation_summary: Optional[dict]


def matrix_chain_order(
    p: List[int], count_operations: bool = False
) -> Tuple[int, List[List[int]], int]:
    """
    Compute the minimum scalar multiplication cost for the matrix
    chain with dimension list p (len(p) = n + 1), and the split
    table used to reconstruct an optimal parenthesization.

    Args:
        p: dimension list.
        count_operations: if True, count the number of (i, j, k)
            cost comparisons evaluated (major computational
            decisions). If False, the counter is still tracked
            internally (cheap) but only reported when requested.

    Returns:
        (min_cost, s, operation_count) where:
        - min_cost is the minimum number of scalar multiplications.
        - s is a 1-indexed (size (n+1) x (n+1)) table where
          s[i][j] is the chosen split point k for subchain (i, j).
        - operation_count is the number of (i, j, k) evaluations
          performed while filling the DP table.
    """
    n = len(p) - 1  # number of matrices
    if n < 1:
        raise ValueError("Need at least one matrix (len(p) >= 2).")
    if n == 1:
        return 0, [[0] * (n + 1) for _ in range(n + 1)], 0

    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]
    operation_count = 0

    for length in range(2, n + 1):          # chain length
        for i in range(1, n - length + 2):  # start index
            j = i + length - 1              # end index
            m[i][j] = float('inf')
            for k in range(i, j):
                operation_count += 1
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                # Strict '<' preserves the smallest k on ties,
                # since k increases in this loop.
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    return m[1][n], s, operation_count


def build_parenthesization(s: List[List[int]], i: int, j: int) -> str:
    """Recursively reconstruct an optimal parenthesization string."""
    if i == j:
        return f"A{i}"
    k = s[i][j]
    left = build_parenthesization(s, i, k)
    right = build_parenthesization(s, k + 1, j)
    return f"({left}{right})"


def solve(p: List[int], include_operation_summary: bool = False) -> MatrixChainResult:
    """
    Solve the matrix chain multiplication problem.

    Args:
        p: dimension list [p0, p1, ..., pn] for n matrices,
           where Ai has shape p[i-1] x p[i].
        include_operation_summary: if True, populate the
            `operation_summary` field with a deterministic summary
            of the computation. If False (default), that field is
            None and all other outputs are exactly as before.

    Returns:
        MatrixChainResult(min_cost, parenthesization, operation_summary)
    """
    n = len(p) - 1
    min_cost, s, operation_count = matrix_chain_order(p)

    if n == 1:
        parenthesization = "A1"
    else:
        parenthesization = build_parenthesization(s, 1, n)

    operation_summary = None
    if include_operation_summary:
        num_subproblems = n * (n - 1) // 2  # number of (i,j) pairs with i<j
        operation_summary = {
            "major_operations": operation_count,
            "subproblems_solved": num_subproblems,
            "num_matrices": n,
        }

    return MatrixChainResult(min_cost, parenthesization, operation_summary)


if __name__ == "__main__":
    p = [30, 35, 15, 5, 10, 20, 25]

    # Feature disabled (default): original behavior unchanged.
    result = solve(p)
    print(f"Dimensions p: {p}")
    print(f"Minimum scalar multiplications: {result.min_cost}")
    print(f"Optimal parenthesization: {result.parenthesization}")
    print(f"operation_summary (disabled): {result.operation_summary}")

    # Feature enabled: adds operation_summary, all else unchanged.
    result_with_summary = solve(p, include_operation_summary=True)
    print(f"\nMinimum scalar multiplications: {result_with_summary.min_cost}")
    print(f"Optimal parenthesization: {result_with_summary.parenthesization}")
    print(f"operation_summary (enabled): {result_with_summary.operation_summary}")

    for test_p in ([10, 20], [40, 20, 30, 10, 30], [1, 2, 3, 4]):
        r = solve(test_p, include_operation_summary=True)
        print(f"\nDimensions p: {test_p}")
        print(f"Minimum scalar multiplications: {r.min_cost}")
        print(f"Optimal parenthesization: {r.parenthesization}")
        print(f"operation_summary: {r.operation_summary}")