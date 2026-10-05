from typing import List


def multiply_polynomials(a: List[int], b: List[int]) -> List[int]:
    """Return the coefficients of a(x) * b(x), lowest degree first."""
    if not a or not b:
        return [0]

    result = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            if bj:
                result[i + j] += ai * bj
    return result


if __name__ == "__main__":
    tests = [
        # (1 + 2x) * (3 - x) = 3 + 5x - 2x^2
        ([1, 2], [3, -1], [3, 5, -2]),
        # (1 + x)^2 = 1 + 2x + x^2
        ([1, 1], [1, 1], [1, 2, 1]),
        # (x - 1)(x + 1) = -1 + x^2
        ([-1, 1], [1, 1], [-1, 0, 1]),
        # multiplication by zero polynomial
        ([0], [5, 7, 9], [0, 0, 0]),
        # constants
        ([-4], [6], [-24]),
        # empty input -> zero polynomial
        ([], [1, 2], [0]),
        # large coefficients stay exact
        ([10**30, -10**30], [10**30, 10**30], [10**60, 0, -10**60]),
    ]
    for a, b, expected in tests:
        got = multiply_polynomials(a, b)
        assert got == expected, (a, b, got, expected)
    print("All tests passed.")