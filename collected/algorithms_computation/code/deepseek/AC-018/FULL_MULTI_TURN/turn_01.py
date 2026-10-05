def multiply_polynomials(a, b):
    """
    Multiply two integer polynomials exactly using direct convolution.
    
    Args:
        a: List of int coefficients for first polynomial (index = power of x)
        b: List of int coefficients for second polynomial (index = power of x)
    
    Returns:
        List of int coefficients for product polynomial
    """
    # Handle empty polynomial edge cases
    if not a or not b:
        return []
    
    # Result degree = (len(a)-1) + (len(b)-1), so length = len(a)+len(b)-1
    result = [0] * (len(a) + len(b) - 1)
    
    # Direct convolution: multiply each pair and accumulate
    for i, coeff_a in enumerate(a):
        if coeff_a == 0:
            continue  # Skip zero coefficients for efficiency
        for j, coeff_b in enumerate(b):
            if coeff_b == 0:
                continue
            result[i + j] += coeff_a * coeff_b
    
    return result


def trim_leading_zeros(poly):
    """Remove trailing zeros (highest degree zero coefficients)."""
    while len(poly) > 1 and poly[-1] == 0:
        poly.pop()
    return poly


def format_polynomial(coeffs):
    """Format coefficient array as a readable polynomial string."""
    if not coeffs:
        return "0"
    
    terms = []
    for power, coeff in enumerate(coeffs):
        if coeff == 0:
            continue
        if power == 0:
            terms.append(f"{coeff}")
        elif power == 1:
            if coeff == 1:
                terms.append("x")
            elif coeff == -1:
                terms.append("-x")
            else:
                terms.append(f"{coeff}x")
        else:
            if coeff == 1:
                terms.append(f"x^{power}")
            elif coeff == -1:
                terms.append(f"-x^{power}")
            else:
                terms.append(f"{coeff}x^{power}")
    
    if not terms:
        return "0"
    
    # Join with proper signs
    result = terms[0]
    for term in terms[1:]:
        if term.startswith("-"):
            result += " - " + term[1:]
        else:
            result += " + " + term
    return result


# ============ Demonstration / Tests ============
if __name__ == "__main__":
    test_cases = [
        # (poly_a, poly_b, expected)
        ([1, 2, 3], [4, 5, 6], [4, 13, 28, 27, 18]),
        ([1, 1], [1, -1], [1, 0, -1]),
        ([2], [3], [6]),
        ([1, 0, 1], [1, 0, 1], [1, 0, 2, 0, 1]),  # (1+x^2)^2
        ([-1, -2], [-3, -4], [3, 10, 8]),
        ([0], [1, 2, 3], [0, 0, 0]),              # zero polynomial
        ([1, 2, 3], [0], [0, 0, 0]),
        ([1, -2, 1], [1, -2, 1], [1, -4, 6, -4, 1]),  # (x-1)^4 expanded
    ]
    
    all_passed = True
    for idx, (a, b, expected) in enumerate(test_cases, 1):
        result = multiply_polynomials(a, b)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"Test {idx}: {status}")
        print(f"  A = {format_polynomial(a)}")
        print(f"  B = {format_polynomial(b)}")
        print(f"  A*B = {format_polynomial(result)}")
        print(f"  Coeffs: {result}")
        if status == "FAIL":
            print(f"  Expected: {expected}")
        print()
    
    print("All tests passed!" if all_passed else "Some tests FAILED.")