def multiply_polynomials(a, b):
    """
    Multiply two integer polynomials exactly.
    
    Args:
        a: list of ints, coefficients of first polynomial (a[0] = constant term)
        b: list of ints, coefficients of second polynomial (b[0] = constant term)
    
    Returns:
        list of ints, coefficients of product polynomial
    """
    if not a or not b:
        return []
    
    # Result degree = deg(a) + deg(b), so length = len(a) + len(b) - 1
    result = [0] * (len(a) + len(b) - 1)
    
    # Direct convolution
    for i, ai in enumerate(a):
        if ai == 0:
            continue  # skip zero coefficients for efficiency
        for j, bj in enumerate(b):
            result[i + j] += ai * bj
    
    return result


def trim(poly):
    """Remove trailing zero coefficients (keep at least [0])."""
    while len(poly) > 1 and poly[-1] == 0:
        poly.pop()
    return poly


def main():
    # Test cases
    test_cases = [
        # (a, b, expected)
        ([1, 2, 3], [4, 5, 6], [4, 13, 28, 27, 18]),
        ([1, -2], [1, 2], [1, 0, -4]),
        ([0], [1, 2, 3], [0, 0, 0]),
        ([2], [3], [6]),
        ([-1, -1], [-1, -1], [1, 2, 1]),
        ([1, 0, 0, 1], [1, 1], [1, 1, 0, 1, 1]),
    ]
    
    for a, b, expected in test_cases:
        got = multiply_polynomials(a, b)
        # For zero-product test, expected length may differ after trim
        got_trimmed = trim(got[:])
        exp_trimmed = trim(expected[:])
        status = "PASS" if got_trimmed == exp_trimmed else "FAIL"
        print(f"{status}: ({a}) * ({b}) = {got}")
        if status == "FAIL":
            print(f"       expected: {expected}")


if __name__ == "__main__":
    main()