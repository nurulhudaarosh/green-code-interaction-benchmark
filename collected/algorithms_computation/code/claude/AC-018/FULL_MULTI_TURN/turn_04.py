from typing import Any, Dict, List, Sequence, Union


def multiply_polynomials(
    a: Sequence[int],
    b: Sequence[int],
    with_summary: bool = False,
) -> Union[List[int], Dict[str, Any]]:
    """
    Multiply two integer polynomials given as ascending-degree coefficient lists
    (a[i] is the coefficient of x^i). Coefficients may be negative.

    Direct coefficient convolution with exact arbitrary-precision ints.
    Output is canonical: no high-degree zero coefficients; the zero polynomial
    is always [0] (including for empty input).

    Tie/ordering rule: `a` is always the outer loop and `b` the inner loop.
    Arguments are never reordered, so summary counts are deterministic.
    Inputs are only read, never mutated (safe when a is b).

    with_summary=False (default): returns List[int].
    with_summary=True: returns {"coefficients": List[int],
                                "operation_summary": {...}}.
    """
    rows_examined = 0
    rows_skipped = 0
    multiply_adds = 0
    zeros_trimmed = 0
    empty_shortcut = False

    if len(a) == 0 or len(b) == 0:
        result: List[int] = [0]
        empty_shortcut = True
    else:
        result = [0] * (len(a) + len(b) - 1)

        for i, ai in enumerate(a):
            rows_examined += 1
            if ai == 0:
                rows_skipped += 1
                continue
            for j, bj in enumerate(b):
                result[i + j] += ai * bj
                multiply_adds += 1

        while len(result) > 1 and result[-1] == 0:
            result.pop()
            zeros_trimmed += 1

    if not with_summary:
        return result

    return {
        "coefficients": result,
        "operation_summary": {
            "rows_examined": rows_examined,
            "rows_skipped": rows_skipped,
            "multiply_adds": multiply_adds,
            "zeros_trimmed": zeros_trimmed,
            "empty_input_shortcut": empty_shortcut,
            "total_operations": rows_examined + multiply_adds + zeros_trimmed,
        },
    }


def _summary(a, b):
    return multiply_polynomials(a, b, with_summary=True)["operation_summary"]


def run_tests() -> None:
    # ---------- Original behavior (regression) ----------
    assert multiply_polynomials([1, 2], [3, -1]) == [3, 5, -2]
    assert multiply_polynomials([-1, 1], [1, 1]) == [-1, 0, 1]
    assert multiply_polynomials([1, 1, 1], [1, -1]) == [1, 0, 0, -1]
    assert multiply_polynomials([1, 0], [2]) == [2]
    assert multiply_polynomials([0, 0], [5]) == [0]
    assert multiply_polynomials([], [5]) == [0]
    assert multiply_polynomials([10**30, -10**30], [10**30]) == [10**60, -10**60]
    assert isinstance(multiply_polynomials([1], [1]), list)
    assert set(multiply_polynomials([1], [1], with_summary=True)) == {
        "coefficients", "operation_summary"}

    # ---------- Repeated values: repeated coefficients ----------
    assert multiply_polynomials([1, 1, 1], [1, 1, 1]) == [1, 2, 3, 2, 1]
    assert multiply_polynomials([2, 2], [2, 2]) == [4, 8, 4]
    assert multiply_polynomials([-1, -1], [-1, -1]) == [1, 2, 1]
    assert _summary([1, 1, 1], [1, 1, 1]) == {
        "rows_examined": 3, "rows_skipped": 0, "multiply_adds": 9,
        "zeros_trimmed": 0, "empty_input_shortcut": False,
        "total_operations": 12,
    }

    # ---------- Repeated values: repeated roots, same object as both args ----------
    p = [1, -1]                                   # x - 1
    p_before = list(p)
    sq = multiply_polynomials(p, p)               # aliasing: a is b
    assert sq == [1, -2, 1]
    assert p == p_before                          # input not mutated
    assert multiply_polynomials(sq, p) == [-1, 3, -3, 1]   # (x-1)^3
    # Interior cancellation from tied contributions: (1+x)^2 (1-x)^2 = (1-x^2)^2
    assert multiply_polynomials([1, 2, 1], [1, -2, 1]) == [1, 0, -2, 0, 1]

    # ---------- Repeated zeros ----------
    assert multiply_polynomials([0, 0, 0], [0, 0]) == [0]
    assert _summary([0, 0, 0], [0, 0]) == {
        "rows_examined": 3, "rows_skipped": 3, "multiply_adds": 0,
        "zeros_trimmed": 3, "empty_input_shortcut": False,
        "total_operations": 6,
    }
    # Repeated trailing zeros collapse to the same canonical form
    assert multiply_polynomials([1, 0, 0], [1, 0, 0]) == [1]
    assert multiply_polynomials([2], [1]) == multiply_polynomials([2, 0, 0], [1]) == [2]
    assert _summary([1, 0, 0], [1, 0, 0]) == {
        "rows_examined": 3, "rows_skipped": 2, "multiply_adds": 3,
        "zeros_trimmed": 4, "empty_input_shortcut": False,
        "total_operations": 10,
    }

    # ---------- Deterministic ties: swapped arguments ----------
    # Same product, equal total_operations, but per-field counts follow the
    # fixed rule that the first argument is the outer loop.
    x2, one = [0, 0, 1], [1]
    assert multiply_polynomials(x2, one) == multiply_polynomials(one, x2) == [0, 0, 1]
    assert _summary(x2, one) == {
        "rows_examined": 3, "rows_skipped": 2, "multiply_adds": 1,
        "zeros_trimmed": 0, "empty_input_shortcut": False,
        "total_operations": 4,
    }
    assert _summary(one, x2) == {
        "rows_examined": 1, "rows_skipped": 0, "multiply_adds": 3,
        "zeros_trimmed": 0, "empty_input_shortcut": False,
        "total_operations": 4,
    }

    # ---------- Determinism, immutability, input types ----------
    u, v = [2, -3, 0, 4], [-1, 5]
    u_copy, v_copy = list(u), list(v)
    first = multiply_polynomials(u, v, with_summary=True)
    for _ in range(3):
        assert multiply_polynomials(u, v, with_summary=True) == first
    assert (u, v) == (u_copy, v_copy)
    assert multiply_polynomials(u, v) == multiply_polynomials(v, u)
    assert multiply_polynomials((1, 2), (3, -1)) == [3, 5, -2]   # tuples work
    assert first["coefficients"] == multiply_polynomials(u, v)

    # Returned list is fresh: mutating it never affects later calls
    out = multiply_polynomials([1, 1], [1, 1])
    out[0] = 999
    assert multiply_polynomials([1, 1], [1, 1]) == [1, 2, 1]


def main() -> None:
    run_tests()
    print("all tests passed")
    print(multiply_polynomials([1, 1, 1], [1, 1, 1], with_summary=True))


if __name__ == "__main__":
    main()