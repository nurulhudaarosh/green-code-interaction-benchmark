def multiply_polynomials(a, b):
    """
    Multiply two integer polynomials exactly and return the coefficient array.
    
    The polynomials are represented by coefficient lists in ascending order:
      a = [a0, a1, ..., an] represents a0 + a1*x + ... + an*x^n
      b = [b0, b1, ..., bm] represents b0 + b1*x + ... + bm*x^m
    
    Returns:
      c = [c0, c1, ..., c_{n+m}] where c[k] = sum_{i+j=k} a[i]*b[j]
    """
    if not isinstance(a, list) or not isinstance(b, list):
        raise TypeError("Inputs must be lists of integers.")
    if any(not isinstance(x, int) for x in a) or any(not isinstance(x, int) for x in b):
        raise TypeError("Coefficients must be integers.")
    if not a or not b:
        return []

    result_len = len(a) + len(b) - 1
    result = [0] * result_len

    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            result[i + j] += ai * bj

    return result


if __name__ == "__main__":
    # Example usage
    p = [1, -2, 3]      # 1 - 2x + 3x^2
    q = [-4, 5]         # -4 + 5x

    product = multiply_polynomials(p, q)
    print(product)      # [-4, 13, -22, 15]