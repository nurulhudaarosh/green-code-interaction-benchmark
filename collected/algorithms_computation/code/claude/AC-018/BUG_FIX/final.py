from typing import List


def multiply_polynomials(a: List[int], b: List[int]) -> List[int]:
    """Return the canonical coefficients of a(x) * b(x), lowest degree first.

    Direct convolution: c[k] = sum(a[i] * b[j] for i + j = k).
    The result has no trailing zeros; the zero polynomial is [0].
    Empty input is treated as the zero polynomial.
    """
    if not a or not b:
        return [0]

    result = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            if bj:
                result[i + j] += ai * bj

    # Canonical form: drop trailing zeros, keep at least one coefficient.
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result


if __name__ == "__main__":
    # Defect demonstration: before the fix, these returned non-canonical lists
    # such as [0, 0, 0], [1, 0, 0], and [1, 0] for the same polynomials.
    tests = [
        ([1, 2], [3, -1], [3, 5, -2]),
        ([1, 1], [1, 1], [1, 2, 1]),
        ([-1, 1], [1, 1], [-1, 0, 1]),
        ([-4], [6], [-24]),
        ([10**30, -10**30], [10**30, 10**30], [10**60, 0, -10**60]),
        # Previously buggy cases, now canonical:
        ([0], [5, 7, 9], [0]),
        ([], [1, 2], [0]),
        ([0, 0], [0, 0, 0], [0]),
        ([1, 0], [1, 0], [1]),
        ([1, 0], [1], [1]),
        ([2, 0, 0], [0, 3, 0], [0, 6]),
    ]
    for a, b, expected in tests:
        got = multiply_polynomials(a, b)
        assert got == expected, (a, b, got, expected)
    print("All tests passed.")