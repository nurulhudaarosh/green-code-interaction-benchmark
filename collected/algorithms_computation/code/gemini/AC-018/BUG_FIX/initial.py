def multiply_polynomials(a: list[int], b: list[int]) -> list[int]:
    """
    Multiplies two integer polynomials using direct linear convolution.
    
    :param a: List of integer coefficients for P(x) in ascending order.
    :param b: List of integer coefficients for Q(x) in ascending order.
    :return: List of integer coefficients for R(x) = P(x) * Q(x) in ascending order.
    """
    if not a or not b:
        return []
    
    len_a = len(a)
    len_b = len(b)
    
    # Allocating memory for product polynomial of degree (len_a + len_b - 2)
    result = [0] * (len_a + len_b - 1)
    
    # Direct coefficient convolution
    for i in range(len_a):
        for j in range(len_b):
            result[i + j] += a[i] * b[j]
            
    return result


# Example Usage & Verification:
if __name__ == "__main__":
    # P(x) = 1 + 2x - 3x^2
    # Q(x) = 4 - x + 5x^2
    poly1 = [1, 2, -3]
    poly2 = [4, -1, 5]
    
    # Expected product: 4 + 7x - 9x^2 + 13x^3 - 15x^4
    # Resulting coefficients: [4, 7, -9, 13, -15]
    product = multiply_polynomials(poly1, poly2)
    print("Product coefficients:", product)