# Problem: Polynomial Multiplication
#
# Given two integer polynomials, multiply them exactly and return the
# coefficient array of the resulting polynomial. Coefficients may be
# positive, zero, or negative.
#
# Key constraints:
# - Inputs contain integer coefficients.
# - Negative coefficients are allowed.
# - The multiplication must be exact.
# - The constraints keep the O(n*m) direct convolution practical.
# - No floating-point arithmetic, randomness, network access, APIs,
#   external services, or human interaction are used.
#
# Required output:
# - A list of integer coefficients representing the product polynomial.
# - If A has length n and B has length m, the result has length n+m-1
#   when both polynomials are non-empty.
#
# Algorithm:
# Use direct coefficient convolution. For every coefficient A[i] and
# B[j], add A[i] * B[j] to result[i + j].
# This takes O(n*m) time and O(n+m) space.
#
# Deterministic behavior:
# Coefficients are processed in increasing index order, and the exact
# integer result is returned without any rounding.


def multiply_polynomials(a, b):
    """
    Multiply two integer polynomials using direct coefficient convolution.

    Polynomial representation:
        [c0, c1, c2, ...]
    represents:
        c0 + c1*x + c2*x^2 + ...

    Returns:
        The coefficient array of a * b.
    """
    if not a or not b:
        return []

    result = [0] * (len(a) + len(b) - 1)

    for i, coefficient_a in enumerate(a):
        for j, coefficient_b in enumerate(b):
            result[i + j] += coefficient_a * coefficient_b

    return result


# Tests

# Basic multiplication:
# (1 + 2x) * (3 + 4x) = 3 + 10x + 8x^2
assert multiply_polynomials([1, 2], [3, 4]) == [3, 10, 8]

# Negative coefficients:
# (2 - 3x) * (-1 + 4x)
# = -2 + 11x - 12x^2
assert multiply_polynomials([2, -3], [-1, 4]) == [-2, 11, -12]

# Zero coefficients:
# (1 + 0x + 2x^2) * (3 + x)
# = 3 + x + 6x^2 + 2x^3
assert multiply_polynomials([1, 0, 2], [3, 1]) == [3, 1, 6, 2]

# Single-coefficient polynomials:
assert multiply_polynomials([7], [-5]) == [-35]

# Zero polynomial:
assert multiply_polynomials([0, 0], [5, -2]) == [0, 0, 0]

# Empty polynomial representation:
assert multiply_polynomials([], [1, 2, 3]) == []
assert multiply_polynomials([1, 2, 3], []) == []

# Mixed positive and negative coefficients:
assert multiply_polynomials([-1, 2, -3], [4, -5]) == [-4, 13, -22, 15]

print("All tests passed.")