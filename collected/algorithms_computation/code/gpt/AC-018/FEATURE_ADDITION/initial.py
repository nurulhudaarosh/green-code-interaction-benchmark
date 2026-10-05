"""
Problem: Exact Polynomial Product

Given two polynomials represented by integer coefficient arrays, multiply them
exactly and return the coefficient array of their product.

Key constraints:
- Coefficients are integers and may be negative.
- The multiplication must be exact.
- The required algorithm is direct coefficient convolution.
- The input sizes are bounded so O(n*m) quadratic computation is practical.
- The solution must be deterministic.
- Use only Python's standard library.
- No network access, APIs, external services, randomness, or human interaction.

Expected output:
- A list of integer coefficients in increasing order of degree.
- For inputs A and B, output C where:
      C[k] = sum(A[i] * B[k-i])
  over all valid i.
- The result has length len(A) + len(B) - 1 for two non-empty inputs.
- Negative coefficients are handled naturally.
- Empty inputs return an empty list.

Algorithm:
Use direct coefficient convolution. For every coefficient A[i], multiply it
by every coefficient B[j] and add the product to C[i + j]. This directly
computes every coefficient of the product in O(n*m) time and O(n+m) space.

Implementation:
"""

from typing import List


def polynomial_product(a: List[int], b: List[int]) -> List[int]:
    """Return the exact coefficient array of a(x) * b(x)."""

    if not a or not b:
        return []

    result = [0] * (len(a) + len(b) - 1)

    for i, coeff_a in enumerate(a):
        for j, coeff_b in enumerate(b):
            result[i + j] += coeff_a * coeff_b

    return result


# Deterministic tests
def _run_tests() -> None:
    assert polynomial_product([1, 2], [3, 4]) == [3, 10, 8]
    assert polynomial_product([1, -2, 3], [4, -5]) == [4, -13, 22, -15]
    assert polynomial_product([0], [7, -2]) == [0, 0]
    assert polynomial_product([], [1, 2]) == []
    assert polynomial_product([1, 2], []) == []
    assert polynomial_product([5], [6]) == [30]
    assert polynomial_product([-1, -2], [-3, 4]) == [3, 2, -8]


if __name__ == "__main__":
    _run_tests()