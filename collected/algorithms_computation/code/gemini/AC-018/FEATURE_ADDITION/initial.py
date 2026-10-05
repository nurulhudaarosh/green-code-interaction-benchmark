def multiply_polynomials(a: list[int], b: list[int]) -> list[int]:
    """
    Multiplies two integer polynomials using direct discrete convolution.
    
    :param a: Coefficient array of the first polynomial [a0, a1, a2, ...]
    :param b: Coefficient array of the second polynomial [b0, b1, b2, ...]
    :return: Coefficient array of the product polynomial [c0, c1, c2, ...]
    """
    if not a or not b:
        return []

    m, n = len(a), len(b)
    result = [0] * (m + n - 1)

    for i in range(m):
        for j in range(n):
            result[i + j] += a[i] * b[j]

    return result


# Example Usage & Verification:
if __name__ == "__main__":
    # P(x) = 1 + 2x - 3x^2
    # Q(x) = -4 + 5x
    # Product: (1 + 2x - 3x^2)(-4 + 5x) = -4 - 3x + 22x^2 - 15x^3
    poly1 = [1, 2, -3]
    poly2 = [-4, 5]
    
    product = multiply_polynomials(poly1, poly2)
    print("Product coefficients:", product)  # Output: [-4, -3, 22, -15]