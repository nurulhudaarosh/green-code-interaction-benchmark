def multiply_polynomials(poly1: list[int], poly2: list[int]) -> list[int]:
    """
    Multiplies two polynomials represented by lists of integer coefficients
    using direct discrete convolution, returning the canonical result list.
    
    :param poly1: Coefficients of the first polynomial [a0, a1, ...].
    :param poly2: Coefficients of the second polynomial [b0, b1, ...].
    :return: Canonical coefficient list for the product polynomial.
    """
    # Handle empty input representations as the zero polynomial
    if not poly1 or not poly2:
        return [0]

    n = len(poly1)
    m = len(poly2)
    
    # Direct coefficient convolution: c_k = sum_{i+j=k} a_i * b_j
    result = [0] * (n + m - 1)
    for i in range(n):
        for j in range(m):
            result[i + j] += poly1[i] * poly2[j]

    # Trim trailing zero coefficients to preserve canonical degree representation
    while len(result) > 1 and result[-1] == 0:
        result.pop()

    return result


if __name__ == "__main__":
    # Test cases demonstrating correct canonical output
    print(multiply_polynomials([1, 2, -3], [-2, 1]))  # Normal product -> [-2, -3, 8, -3]
    print(multiply_polynomials([0, 0], [1, 2]))       # Zero product   -> [0]
    print(multiply_polynomials([], [1, 2]))           # Empty input   -> [0]