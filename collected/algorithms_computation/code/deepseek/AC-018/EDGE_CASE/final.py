def multiply_polynomials(a, b):
    """
    Multiply two integer polynomials given as coefficient lists
    (index = power of x, ascending order).

    Determinism guarantees:
      - Outer loop over a in increasing index order.
      - Inner loop over b in increasing index order.
      - Ties at the same output power k = i + j are accumulated in
        lexicographic (i, j) order.
      - Output length is exactly len(a) + len(b) - 1, preserving any
        leading/trailing zeros that arise from the exact product.
      - Repeated input values are preserved positionally; no dedup.
    """
    if not a or not b:
        return []

    result = [0] * (len(a) + len(b) - 1)

    # Fixed iteration order -> deterministic tie accumulation.
    for i in range(len(a)):
        ai = a[i]
        if ai == 0:
            # Zero terms contribute nothing; skipping them does not
            # change the result and keeps the execution path stable.
            continue
        for j in range(len(b)):
            result[i + j] += ai * b[j]

    return result


# ----------------------------------------------------------------------
# Tests — original cases + explicit repeated-value and tie cases
# ----------------------------------------------------------------------
def _run_tests():
    # --- Original / basic cases ---
    assert multiply_polynomials([1, 2], [3, 4]) == [3, 10, 8]
    assert multiply_polynomials([5], [1, 2, 3]) == [5, 10, 15]
    assert multiply_polynomials([1], [1, 2, 3]) == [1, 2, 3]
    assert multiply_polynomials([1, -2], [3, -4]) == [3, -10, 8]
    assert multiply_polynomials([0, 1], [0, 0, 1]) == [0, 0, 0, 1]
    assert multiply_polynomials([0], [1, 2, 3]) == [0, 0, 0]
    assert multiply_polynomials([], [1, 2]) == []
    assert multiply_polynomials([1, 2], []) == []
    assert multiply_polynomials([1, 1], [1, 1]) == [1, 2, 1]
    assert multiply_polynomials([1, 1], [1, 2, 1]) == [1, 3, 3, 1]
    assert multiply_polynomials([2, 3, 4], [5, 6]) == [10, 27, 38, 24]

    # --- Repeated values in a single input ---
    # [2, 2, 2] represents 2 + 2x + 2x^2
    # times [3, 3] = 3 + 3x  ->  6 + 12x + 12x^2 + 6x^3
    assert multiply_polynomials([2, 2, 2], [3, 3]) == [6, 12, 12, 6]

    # All-equal inputs, symmetric check
    # [1, 1, 1] * [1, 1, 1] = [1, 2, 3, 2, 1]
    assert multiply_polynomials([1, 1, 1], [1, 1, 1]) == [1, 2, 3, 2, 1]

    # Repeated negatives: [-1, -1] * [-1, -1] = [1, 2, 1]
    assert multiply_polynomials([-1, -1], [-1, -1]) == [1, 2, 1]

    # --- Deterministic tie cases (multiple (i,j) -> same output power) ---
    # Power 2 receives contributions from (0,2),(1,1),(2,0).
    # a = [1, 2, 3], b = [4, 5, 6]
    #   k=0: 1*4 = 4
    #   k=1: 1*5 + 2*4 = 13
    #   k=2: 1*6 + 2*5 + 3*4 = 6 + 10 + 12 = 28
    #   k=3: 2*6 + 3*5 = 12 + 15 = 27
    #   k=4: 3*6 = 18
    assert multiply_polynomials([1, 2, 3], [4, 5, 6]) == [4, 13, 28, 27, 18]

    # Ties that sum to zero (cancellation must be exact, not reordered)
    # a = [1, -1], b = [1, 1] -> [1, 0, -1]
    assert multiply_polynomials([1, -1], [1, 1]) == [1, 0, -1]

    # Ties with identical magnitudes and signs
    # a = [2, 3], b = [2, 3] -> [4, 12, 9]
    assert multiply_polynomials([2, 3], [2, 3]) == [4, 12, 9]

    # Many-way tie at the middle coefficient
    # a = b = [1, 1, 1, 1] -> binomial row [1, 2, 3, 4, 3, 2, 1]
    assert multiply_polynomials([1, 1, 1, 1], [1, 1, 1, 1]) == [1, 2, 3, 4, 3, 2, 1]

    # Repeated values + ties combined
    # a = [5, 5, 5], b = [5, 5, 5] -> 25 * [1,2,3,2,1] = [25,50,75,50,25]
    assert multiply_polynomials([5, 5, 5], [5, 5, 5]) == [25, 50, 75, 50, 25]

    # --- Determinism check: same inputs, repeated calls, identical output ---
    import copy
    a_in = [1, -2, 3, -4, 5]
    b_in = [5, -4, 3, -2, 1]
    a_snapshot = copy.deepcopy(a_in)
    b_snapshot = copy.deepcopy(b_in)
    first = multiply_polynomials(a_in, b_in)
    for _ in range(50):
        assert multiply_polynomials(a_in, b_in) == first
    # Inputs must not be mutated
    assert a_in == a_snapshot and b_in == b_snapshot

    # --- Output-length rule preserved (no zero-trimming) ---
    # Leading/trailing zeros from zero coefficients are kept.
    # [0, 1] * [0, 1] = [0, 0, 1]  (length 3, not trimmed to [1])
    assert multiply_polynomials([0, 1], [0, 1]) == [0, 0, 1]
    # Zero polynomial retains full length
    assert multiply_polynomials([0, 0], [0, 0, 0]) == [0, 0, 0, 0]

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()