"""
Problem:
Multiply two integer polynomials exactly and return the coefficient array.
Coefficients may be negative.

Key constraints:
- Inputs contain integers, including negative values.
- Use direct coefficient convolution.
- The quadratic O(n*m) computation is practical under the given constraints.
- The solution must be deterministic.
- Use only Python's standard library.
- No network access, APIs, external services, randomness, or human interaction.

Required output:
- Return a list containing the coefficients of the exact product.
- If A has length n and B has length m, the result has length n + m - 1
  for non-empty inputs.
- Coefficient i of the result is:
      result[i] = sum(A[j] * B[i-j])
  over all valid j.
"""


def exact_polynomial_product(a, b):
    """
    Multiply two integer polynomials using direct coefficient convolution.

    Parameters:
        a: list of integer coefficients
        b: list of integer coefficients

    Returns:
        list of integer coefficients of a * b
    """
    if not a or not b:
        return []

    result = [0] * (len(a) + len(b) - 1)

    # Direct coefficient convolution.
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i + j] += x * y

    return result


# Tests
assert exact_polynomial_product([1, 2], [3, 4]) == [3, 10, 8]
assert exact_polynomial_product([1, -2, 3], [-2, 4]) == [-2, 8, -14, 12]
assert exact_polynomial_product([5], [-3]) == [-15]
assert exact_polynomial_product([0, 0], [1, 2]) == [0, 0, 0]
assert exact_polynomial_product([], [1, 2]) == []
assert exact_polynomial_product([1, 2], []) == []

# Example:
# (1 + 2x) * (3 + 4x) = 3 + 10x + 8x^2
print(exact_polynomial_product([1, 2], [3, 4]))