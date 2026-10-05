from typing import List, Sequence


def multiply_polynomials(a: Sequence[int], b: Sequence[int],
                         trim: bool = False) -> List[int]:
    """
    Multiply two integer polynomials given as ascending-degree coefficient lists.

    a[i] is the coefficient of x^i. Returns the exact product's coefficients.
    If either input is empty (zero polynomial), returns [0].
    If trim is True, high-degree zero coefficients are removed (keeping at
    least one element).
    """
    if len(a) == 0 or len(b) == 0:
        return [0]

    result = [0] * (len(a) + len(b) - 1)

    # Iterate over the shorter list in the outer loop for slightly less overhead.
    if len(a) < len(b):
        a, b = b, a  # multiplication is commutative; result unchanged

    for j, bj in enumerate(b):
        if bj == 0:
            continue  # skip zero terms; contributes nothing
        for i, ai in enumerate(a):
            result[i + j] += ai * bj

    if trim:
        while len(result) > 1 and result[-1] == 0:
            result.pop()

    return result


def main() -> None:
    # (1 + 2x)(3 - x) = 3 + 5x - 2x^2
    assert multiply_polynomials([1, 2], [3, -1]) == [3, 5, -2]

    # (x - 1)(x + 1) = -1 + 0x + x^2
    assert multiply_polynomials([-1, 1], [1, 1]) == [-1, 0, 1]

    # (1 + x + x^2)(1 - x) = 1 - x^3
    assert multiply_polynomials([1, 1, 1], [1, -1]) == [1, 0, 0, -1]

    # Zero polynomial
    assert multiply_polynomials([], [1, 2, 3]) == [0]
    assert multiply_polynomials([0, 0], [5]) == [0, 0]
    assert multiply_polynomials([0, 0], [5], trim=True) == [0]

    # Large coefficients stay exact
    big = 10**30
    assert multiply_polynomials([big, -big], [big]) == [big * big, -big * big]

    # Commutativity check (argument swap must not change the result)
    p, q = [2, -3, 0, 4], [-1, 5]
    assert multiply_polynomials(p, q) == multiply_polynomials(q, p)

    print(multiply_polynomials([1, 2], [3, -1]))  # [3, 5, -2]


if __name__ == "__main__":
    main()