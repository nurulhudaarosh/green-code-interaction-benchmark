from typing import List


def multiply_polynomials(a: List[int], b: List[int]) -> List[int]:
    """Multiply two integer polynomials exactly.

    a[i] and b[i] are coefficients of x^i (ascending order).
    Returns the coefficient list of the product, length len(a)+len(b)-1.
    An empty input is treated as the zero polynomial, giving [0].
    """
    if not a or not b:
        return [0]

    result = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            result[i + j] += ai * bj
    return result


if __name__ == "__main__":
    # (1 + 2x)(3 - x) = 3 + 5x - 2x^2
    assert multiply_polynomials([1, 2], [3, -1]) == [3, 5, -2]
    # (1 - x)(1 + x) = 1 - x^2
    assert multiply_polynomials([1, -1], [1, 1]) == [1, 0, -1]
    # Zero polynomial
    assert multiply_polynomials([0], [5, 7]) == [0, 0]
    # Empty input
    assert multiply_polynomials([], [1, 2]) == [0]
    # Big integers stay exact
    assert multiply_polynomials([10**30, -1], [10**30]) == [10**60, -(10**30)]
    print("All tests passed.")