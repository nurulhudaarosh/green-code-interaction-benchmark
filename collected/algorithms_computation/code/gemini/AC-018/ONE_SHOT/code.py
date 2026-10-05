def multiply_polynomials(A: list[int], B: list[int]) -> list[int]:
    """
    Multiplies two polynomials represented as lists of integer coefficients.
    
    :param A: List of coefficients for polynomial A(x) in ascending degree order.
    :param B: List of coefficients for polynomial B(x) in ascending degree order.
    :return: Exact product polynomial coefficient list C(x) = A(x) * B(x).
    """
    if not A or not B:
        return []

    len_a, len_b = len(A), len(B)
    result = [0] * (len_a + len_b - 1)

    for i in range(len_a):
        for j in range(len_b):
            result[i + j] += A[i] * B[j]

    return result


# Example Usage & Verification:
if __name__ == "__main__":
    # Example 1: (1 - 2x + 3x^2) * (4 + 5x)
    # Expected: 4 - 3x + 2x^2 + 15x^3
    poly1 = [1, -2, 3]
    poly2 = [4, 5]
    print("Result 1:", multiply_polynomials(poly1, poly2))  # [4, -3, 2, 15]

    # Example 2: (x^2 - 1) * (x + 3) -> (-1 + 0x + 1x^2) * (3 + 1x)
    # Expected: -3 - 1x + 3x^2 + 1x^3
    poly3 = [-1, 0, 1]
    poly4 = [3, 1]
    print("Result 2:", multiply_polynomials(poly3, poly4))  # [-3, -1, 3, 1]