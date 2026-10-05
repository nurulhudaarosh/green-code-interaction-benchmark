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

    with_summary=False (default): returns List[int], identical to the original.
    with_summary=True: returns {"coefficients": List[int],
                                "operation_summary": {...}}.

    Deterministic; standard library only; no I/O, network, or randomness.
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

        # Canonical form: drop high-degree zeros, keep at least one coefficient.
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


def main() -> None:
    # --- Original behavior, feature disabled (plain list, unchanged) ---
    assert multiply_polynomials([1, 2], [3, -1]) == [3, 5, -2]
    assert multiply_polynomials([-1, 1], [1, 1]) == [-1, 0, 1]
    assert multiply_polynomials([1, 1, 1], [1, -1]) == [1, 0, 0, -1]
    assert multiply_polynomials([1, 0], [2]) == [2]
    assert multiply_polynomials([0, 0], [5]) == [0]
    assert multiply_polynomials([], [5]) == [0]
    assert multiply_polynomials([0, 0, 0], [0]) == [0]
    assert multiply_polynomials([10**30, -10**30], [10**30]) == [10**60, -10**60]
    p, q = [2, -3, 0, 4], [-1, 5]
    assert multiply_polynomials(p, q) == multiply_polynomials(q, p)
    assert multiply_polynomials([1, 2, 0, 0], [3, -1, 0]) == [3, 5, -2]
    assert multiply_polynomials([1, 2], [3, -1], with_summary=False) == [3, 5, -2]

    # --- Feature enabled ---
    r = multiply_polynomials([1, 2], [3, -1], with_summary=True)
    assert r["coefficients"] == [3, 5, -2]
    assert r["operation_summary"] == {
        "rows_examined": 2, "rows_skipped": 0, "multiply_adds": 4,
        "zeros_trimmed": 0, "empty_input_shortcut": False, "total_operations": 6,
    }

    r = multiply_polynomials([1, 0], [2], with_summary=True)
    assert r["coefficients"] == [2]
    assert r["operation_summary"] == {
        "rows_examined": 2, "rows_skipped": 1, "multiply_adds": 1,
        "zeros_trimmed": 1, "empty_input_shortcut": False, "total_operations": 4,
    }

    r = multiply_polynomials([0, 0], [5], with_summary=True)
    assert r["coefficients"] == [0]
    assert r["operation_summary"]["rows_skipped"] == 2
    assert r["operation_summary"]["multiply_adds"] == 0
    assert r["operation_summary"]["zeros_trimmed"] == 1
    assert r["operation_summary"]["total_operations"] == 3

    r = multiply_polynomials([], [5], with_summary=True)
    assert r["coefficients"] == [0]
    assert r["operation_summary"] == {
        "rows_examined": 0, "rows_skipped": 0, "multiply_adds": 0,
        "zeros_trimmed": 0, "empty_input_shortcut": True, "total_operations": 0,
    }

    # Coefficients identical with and without the summary; summary is repeatable
    assert multiply_polynomials(p, q, with_summary=True)["coefficients"] == \
        multiply_polynomials(p, q)
    assert multiply_polynomials(p, q, with_summary=True) == \
        multiply_polynomials(p, q, with_summary=True)

    print(multiply_polynomials([1, 2], [3, -1], with_summary=True))


if __name__ == "__main__":
    main()