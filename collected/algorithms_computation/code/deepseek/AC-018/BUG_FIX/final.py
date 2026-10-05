def multiply_polynomials(a, b):
    """
    Multiply two integer polynomials exactly and return the coefficient array.

    Representation (ascending degree order):
      a = [a0, a1, ..., an]  ->  a0 + a1*x + ... + an*x^n
      b = [b0, b1, ..., bm]  ->  b0 + b1*x + ... + bm*x^m

    Returns:
      c = [c0, c1, ..., c_{n+m}] with c[k] = sum_{i+j=k} a[i]*b[j]

    Guarantees:
      - Exact integer arithmetic (no float, no modular reduction).
      - Deterministic accumulation order: i ascending, then j ascending.
      - Empty input is treated as the zero polynomial and returns [0].
    """
    if not isinstance(a, list) or not isinstance(b, list):
        raise TypeError("Inputs must be lists of integers.")
    if any(not isinstance(x, int) for x in a) or any(not isinstance(x, int) for x in b):
        raise TypeError("Coefficients must be integers.")

    # Normalize empty lists to the zero polynomial representation [0].
    if not a:
        a = [0]
    if not b:
        b = [0]

    result_len = len(a) + len(b) - 1
    result = [0] * result_len

    # Deterministic tie handling: fixed nested loop order (i asc, then j asc).
    # This makes accumulation into result[i + j] reproducible.
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            result[i + j] += ai * bj

    return result


if __name__ == "__main__":
    # Small valid examples
    print(multiply_polynomials([], [5, -3]))          # [0]
    print(multiply_polynomials([0, 0, 1], [0, 1, 0])) # [0, 0, 0, 1]

    p = [1, -2, 3]      # 1 - 2x + 3x^2
    q = [-4, 5]         # -4 + 5x
    print(multiply_polynomials(p, q))                 # [-4, 13, -22, 15]