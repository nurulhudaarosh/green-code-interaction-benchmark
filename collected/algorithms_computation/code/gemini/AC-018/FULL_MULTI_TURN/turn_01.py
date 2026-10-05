def multiply_polynomials(poly1: list[int], poly2: list[int]) -> list[int]:
    """
    Multiplies two polynomials represented by lists of integer coefficients.
    Coefficients are ordered by degree from low to high (index i = degree i).
    
    :param poly1: List of integer coefficients for the first polynomial.
    :param poly2: List of integer coefficients for the second polynomial.
    :return: List of integer coefficients for the product polynomial.
    """
    if not poly1 or not poly2:
        return []

    n = len(poly1)
    m = len(poly2)
    
    # The degree of the product is (n - 1) + (m - 1), so length is n + m - 1
    result = [0] * (n + m - 1)
    
    for i in range(n):
        for j in range(m):
            result[i + j] += poly1[i] * poly2[j]
            
    return result


# Example Usage:
# P1(x) = 1 + 2x - 3x^2   -> [1, 2, -3]
# P2(x) = -2 + x          -> [-2, 1]
# Product: -2 - 3x + 8x^2 - 3x^3 -> [-2, -3, 8, -3]

if __name__ == "__main__":
    p1 = [1, 2, -3]
    p2 = [-2, 1]
    product = multiply_polynomials(p1, p2)
    print("Product coefficients:", product)