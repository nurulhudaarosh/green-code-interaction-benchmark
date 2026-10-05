"""
Exact Polynomial Product

Original problem:
Multiply two integer polynomials exactly and return the coefficient array.
Coefficients may be negative.

Key requirements:
- Use direct coefficient convolution.
- The computation is O(n * m), which is practical under the given constraints.
- Preserve exact integer arithmetic.
- Return the coefficients in increasing order of degree.
- Handle negative coefficients correctly.
- The solution must be deterministic.
- There are no optimization-based or choice-based ties in polynomial
  multiplication: every coefficient is uniquely determined by convolution.
  Therefore, repeated values and any apparent ties must produce the same
  uniquely determined coefficient array every time.
- Empty input is handled deterministically by returning [].
- Use only the Python standard library.
- No network access, APIs, external services, randomness, or human interaction.

Required output:
- For non-empty polynomials A and B, return a list of length
  len(A) + len(B) - 1.
- result[i] is the exact coefficient of x^i in A(x) * B(x).
- For empty input, return [].
"""


def exact_polynomial_product(a, b):
    """
    Multiply two integer polynomials using direct coefficient convolution.

    Coefficients are stored in increasing degree order:
        [c0, c1, c2] represents c0 + c1*x + c2*x^2.

    Repeated values require no special handling because each pair of
    coefficients contributes independently to its unique output index.
    Deterministic tie handling is naturally preserved because the output
    coefficient is the exact sum of all such contributions.
    """
    if not a or not b:
        return []

    result = [0] * (len(a) + len(b) - 1)

    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i + j] += x * y

    return result


# ------------------------------------------------------------
# Original behavior tests
# ------------------------------------------------------------

# Basic multiplication:
# (1 + 2x)(3 + 4x) = 3 + 10x + 8x^2
assert exact_polynomial_product([1, 2], [3, 4]) == [3, 10, 8]

# Negative coefficients:
# (1 - 2x + 3x^2)(-2 + 4x)
# = -2 + 8x - 14x^2 + 12x^3
assert exact_polynomial_product(
    [1, -2, 3],
    [-2, 4]
) == [-2, 8, -14, 12]

# Single coefficients.
assert exact_polynomial_product([5], [-3]) == [-15]

# Zero coefficients.
assert exact_polynomial_product([0, 0], [1, 2]) == [0, 0, 0]

# Empty input.
assert exact_polynomial_product([], [1, 2]) == []
assert exact_polynomial_product([1, 2], []) == []


# ------------------------------------------------------------
# Difficult case: repeated values
# ------------------------------------------------------------

# Repeated coefficients:
# (1 + x + x^2)(1 + x + x^2)
# = 1 + 2x + 3x^2 + 2x^3 + x^4
assert exact_polynomial_product(
    [1, 1, 1],
    [1, 1, 1]
) == [1, 2, 3, 2, 1]

# All coefficients repeated:
# (2 + 2x + 2x^2)(2 + 2x)
# = 4 + 8x + 8x^2 + 4x^3
assert exact_polynomial_product(
    [2, 2, 2],
    [2, 2]
) == [4, 8, 8, 4]

# Repeated negative values.
assert exact_polynomial_product(
    [-1, -1],
    [-1, -1]
) == [1, 2, 1]


# ------------------------------------------------------------
# Difficult case: deterministic ties
# ------------------------------------------------------------

# Multiple coefficient pairs contribute to the same degree.
# Every contribution must be accumulated into the same unique
# result position, regardless of the repeated values.
assert exact_polynomial_product(
    [1, 1],
    [1, 1]
) == [1, 2, 1]

# Symmetric inputs produce the same deterministic result.
a = [2, -1, 2, -1]
b = [3, 3, 3]

assert exact_polynomial_product(a, b) == [
    6, 3, 9, 3, 6, -3
]

# Repeating the same computation must return exactly the same result.
expected = exact_polynomial_product([1, 1, 1], [1, 1, 1])
for _ in range(5):
    assert exact_polynomial_product([1, 1, 1], [1, 1, 1]) == expected

# Swapping the two polynomials must not change the mathematical product.
assert exact_polynomial_product(
    [2, 2, 2],
    [1, 1, 1]
) == exact_polynomial_product(
    [1, 1, 1],
    [2, 2, 2]
)


# ------------------------------------------------------------
# Boundary case with repeated zeros
# ------------------------------------------------------------

assert exact_polynomial_product(
    [0, 0, 0],
    [0, 0]
) == [0, 0, 0, 0]


# Example output:
# (1 + 2x) * (3 + 4x) = 3 + 10x + 8x^2
print(exact_polynomial_product([1, 2], [3, 4]))