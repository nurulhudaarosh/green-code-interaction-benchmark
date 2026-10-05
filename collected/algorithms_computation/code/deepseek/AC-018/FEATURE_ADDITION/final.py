def multiply_polynomials(a, b, return_summary=False):
    """
    Multiply two integer polynomials exactly via direct coefficient convolution.

    Args:
        a: list of ints, coefficients of first polynomial (a[0] = constant term)
        b: list of ints, coefficients of second polynomial (b[0] = constant term)
        return_summary: bool. If False (default), returns the coefficient array
                        exactly as in the original specification. If True, returns
                        a tuple (coefficients, operation_summary).

    Returns:
        If return_summary is False:
            list of ints -- product coefficients.
        If return_summary is True:
            (list of ints, dict) where the dict is the operation_summary.
    """
    if not a or not b:
        coefficients = []
        if return_summary:
            summary = {
                "input_length_a": len(a),
                "input_length_b": len(b),
                "output_length": 0,
                "pairs_considered": 0,
                "multiply_accumulate_ops": 0,
                "zero_skip_decisions": 0,
                "total_major_operations": 0,
                "empty_input": True,
            }
            return coefficients, summary
        return coefficients

    m, n = len(a), len(b)
    result = [0] * (m + n - 1)

    pairs_considered = 0
    mac_ops = 0        # multiply-and-accumulate operations (major ops)
    skip_decisions = 0 # zero-coefficient skip decisions

    for i, ai in enumerate(a):
        if ai == 0:
            skip_decisions += n  # skipped all n pairs for this row
            continue
        for j, bj in enumerate(b):
            pairs_considered += 1
            result[i + j] += ai * bj
            mac_ops += 1

    coefficients = result

    if not return_summary:
        return coefficients

    summary = {
        "input_length_a": m,
        "input_length_b": n,
        "output_length": len(result),
        "pairs_considered": pairs_considered,
        "multiply_accumulate_ops": mac_ops,
        "zero_skip_decisions": skip_decisions,
        "total_major_operations": mac_ops,  # arithmetic ops are the major ops
        "empty_input": False,
    }
    return coefficients, summary


def trim(poly):
    """Remove trailing zero coefficients (keep at least [0])."""
    while len(poly) > 1 and poly[-1] == 0:
        poly.pop()
    return poly


def main():
    test_cases = [
        ([1, 2, 3], [4, 5, 6], [4, 13, 28, 27, 18]),
        ([1, -2], [1, 2], [1, 0, -4]),
        ([0], [1, 2, 3], [0, 0, 0]),
        ([2], [3], [6]),
        ([-1, -1], [-1, -1], [1, 2, 1]),
        ([1, 0, 0, 1], [1, 1], [1, 1, 0, 1, 1]),
    ]

    print("=== Original behavior (feature disabled) ===")
    for a, b, expected in test_cases:
        got = multiply_polynomials(a, b)  # default: plain array
        got_trimmed = trim(got[:])
        exp_trimmed = trim(expected[:])
        status = "PASS" if got_trimmed == exp_trimmed else "FAIL"
        print(f"{status}: ({a}) * ({b}) = {got}")
        if status == "FAIL":
            print(f"       expected: {expected}")

    print()
    print("=== Extended behavior (feature enabled) ===")
    for a, b, expected in test_cases:
        got, summary = multiply_polynomials(a, b, return_summary=True)
        print(f"({a}) * ({b}) = {got}")
        print(f"    operation_summary: {summary}")


if __name__ == "__main__":
    main()