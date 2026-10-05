from typing import List


def multiply_polynomials(a: List[int], b: List[int]) -> List[int]:
    """Return the exact coefficient array of the product of polynomials a and b.

    a[i] is the coefficient of x^i. Result has length len(a) + len(b) - 1,
    or [] if either input is empty.

    Repeated values: every (i, j) pair contributes independently; nothing is
    deduplicated. Ties (several pairs landing on the same index i + j) are
    resolved deterministically by accumulating in increasing i, then
    increasing j. Integer addition is exact, so the result is order-independent.
    """
    if not a or not b:
        return []

    result = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue  # contributes nothing; output length is unaffected
        for j, bj in enumerate(b):
            result[i + j] += ai * bj
    return result


def _self_test() -> None:
    # --- Original tests (unchanged) ---
    assert multiply_polynomials([1, 2], [3, -1]) == [3, 5, -2]
    assert multiply_polynomials([-1, 1], [1, 1]) == [-1, 0, 1]
    assert multiply_polynomials([5], [1, -2, 3]) == [5, -10, 15]
    assert multiply_polynomials([0, 0], [1, 2]) == [0, 0, 0]
    assert multiply_polynomials([], [1, 2]) == []
    big = 10**30
    assert multiply_polynomials([big], [big]) == [big * big]

    # --- Repeated values ---
    # (2 + 2x + 2x^2)(2 + 2x + 2x^2) = 4 + 8x + 12x^2 + 8x^3 + 4x^4
    assert multiply_polynomials([2, 2, 2], [2, 2, 2]) == [4, 8, 12, 8, 4]
    # All ones: convolution counts the pairs per slot
    assert multiply_polynomials([1, 1, 1, 1], [1, 1, 1]) == [1, 2, 3, 3, 2, 1]
    # Repeated negative values
    assert multiply_polynomials([-3, -3], [-3, -3]) == [9, 18, 9]
    # All zeros, repeated: length preserved, no trimming
    assert multiply_polynomials([0, 0, 0], [0, 0]) == [0, 0, 0, 0]
    # Repeated values with trailing zeros preserved
    assert multiply_polynomials([1, 0, 0], [1, 0]) == [1, 0, 0, 0]

    # --- Deterministic ties (many pairs land on the same index) ---
    # Cancellation tie: x^1 slot gets 1*(-1) + 1*1 = 0, kept as an explicit 0
    assert multiply_polynomials([1, 1], [-1, 1]) == [-1, 0, 1]
    # Symmetric inputs give a palindromic result
    r = multiply_polynomials([1, 2, 1], [1, 2, 1])
    assert r == [1, 4, 6, 4, 1] and r == r[::-1]
    # Commutativity: swapping arguments gives an identical result
    p, q = [3, -1, 3, 3], [2, 2, -5]
    assert multiply_polynomials(p, q) == multiply_polynomials(q, p)
    # Determinism: repeated calls agree and inputs are not mutated
    p_copy, q_copy = p[:], q[:]
    first = multiply_polynomials(p, q)
    assert multiply_polynomials(p, q) == first
    assert p == p_copy and q == q_copy
    # Order of accumulation does not matter: compare with reversed-loop reference
    def reference(a, b):
        res = [0] * (len(a) + len(b) - 1)
        for j in range(len(b) - 1, -1, -1):
            for i in range(len(a) - 1, -1, -1):
                res[i + j] += a[i] * b[j]
        return res
    assert multiply_polynomials(p, q) == reference(p, q)


if __name__ == "__main__":
    _self_test()
    print(multiply_polynomials([1, 2, 3], [4, -5, 6]))  # [4, 3, 8, -3, 18]
    print("all tests passed")