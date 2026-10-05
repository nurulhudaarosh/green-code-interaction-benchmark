def multiply_polynomials(a, b):
    """
    Multiply two integer polynomials given as coefficient lists
    (index = power of x, ascending order). Returns the product's
    coefficient list.
    """
    # Edge case: if either polynomial is empty, the product is empty
    if not a or not b:
        return []

    # Result has degree (len(a)-1) + (len(b)-1), so length len(a)+len(b)-1
    result = [0] * (len(a) + len(b) - 1)

    # Direct convolution: accumulate products at the correct power index
    for i, coeff_a in enumerate(a):
        if coeff_a == 0:
            continue  # minor optimization; skip zero terms
        for j, coeff_b in enumerate(b):
            result[i + j] += coeff_a * coeff_b

    return result


def _run_tests():
    # Basic case
    assert multiply_polynomials([1, 2], [3, 4]) == [3, 10, 8]

    # Constant * polynomial
    assert multiply_polynomials([5], [1, 2, 3]) == [5, 10, 15]

    # Identity (multiply by 1)
    assert multiply_polynomials([1], [1, 2, 3]) == [1, 2, 3]

    # Negative coefficients
    assert multiply_polynomials([1, -2], [3, -4]) == [3, -10, 8]

    # Zeros inside
    assert multiply_polynomials([0, 1], [0, 0, 1]) == [0, 0, 0, 1]

    # Zero polynomial
    assert multiply_polynomials([0], [1, 2, 3]) == [0, 0, 0]

    # Empty inputs
    assert multiply_polynomials([], [1, 2]) == []
    assert multiply_polynomials([1, 2], []) == []

    # Larger case: (1 + x)^2 = 1 + 2x + x^2
    assert multiply_polynomials([1, 1], [1, 1]) == [1, 2, 1]

    # (1 + x)^3 = 1 + 3x + 3x^2 + x^3
    assert multiply_polynomials([1, 1], [1, 2, 1]) == [1, 3, 3, 1]

    # Verify against known: (2 + 3x + 4x^2)(5 + 6x) = 10 + 27x + 38x^2 + 24x^3
    assert multiply_polynomials([2, 3, 4], [5, 6]) == [10, 27, 38, 24]

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()