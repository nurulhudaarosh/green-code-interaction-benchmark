from typing import List


def multiply_polynomials(a: List[int], b: List[int]) -> List[int]:
    """Return the exact coefficient array of the product of polynomials a and b.

    a[i] is the coefficient of x^i. Result has length len(a) + len(b) - 1,
    or [] if either input is empty.
    """
    if not a or not b:
        return []

    result = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue  # nothing to contribute
        for j, bj in enumerate(b):
            result[i + j] += ai * bj
    return result


def _self_test() -> None:
    # (1 + 2x)(3 - x) = 3 + 5x - 2x^2
    assert multiply_polynomials([1, 2], [3, -1]) == [3, 5, -2]
    # (x - 1)(x + 1) = -1 + 0x + x^2
    assert multiply_polynomials([-1, 1], [1, 1]) == [-1, 0, 1]
    # Constant times polynomial
    assert multiply_polynomials([5], [1, -2, 3]) == [5, -10, 15]
    # Zero polynomial keeps length
    assert multiply_polynomials([0, 0], [1, 2]) == [0, 0, 0]
    # Empty input
    assert multiply_polynomials([], [1, 2]) == []
    # Big integers stay exact
    big = 10**30
    assert multiply_polynomials([big], [big]) == [big * big]


if __name__ == "__main__":
    _self_test()
    print(multiply_polynomials([1, 2, 3], [4, -5, 6]))  # [4, 3, 8, -3, 18]