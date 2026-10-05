def multiply_polynomials(p: list[int], q: list[int]) -> list[int]:
    """
    Multiplies two integer polynomials using direct coefficient convolution.
    
    :param p: Coefficient array of first polynomial (ascending order of degree)
    :param q: Coefficient array of second polynomial (ascending order of degree)
    :return: Exact coefficient array of the product polynomial
    """
    if not p or not q:
        return []
    
    len_p = len(p)
    len_q = len(q)
    
    # Initialize output list for polynomial of degree (len_p - 1) + (len_q - 1)
    result = [0] * (len_p + len_q - 1)
    
    # Direct convolution
    for i in range(len_p):
        for j in range(len_q):
            result[i + j] += p[i] * q[j]
            
    return result


# Example Usage & Verification:
if __name__ == "__main__":
    # P(x) = 1 - 2x + 3x^2
    # Q(x) = 4 + 5x
    # P(x) * Q(x) = 4 - 3x + 2x^2 + 15x^3
    poly1 = [1, -2, 3]
    poly2 = [4, 5]
    
    product = multiply_polynomials(poly1, poly2)
    print("Poly 1:", poly1)
    print("Poly 2:", poly2)
    print("Product:", product)
    # Output: [4, -3, 2, 15]