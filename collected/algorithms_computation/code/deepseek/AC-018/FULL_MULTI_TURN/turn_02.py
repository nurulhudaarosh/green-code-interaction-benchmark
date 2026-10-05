"""
Exact Polynomial Product
========================
Multiply two integer polynomials exactly using direct coefficient convolution.

Rules enforced:
  1. Exact integer arithmetic (no floats, no rounding).
  2. Negative coefficients supported; signs preserved.
  3. Output length is EXACTLY len(a) + len(b) - 1, interior zeros preserved.
  4. Deterministic accumulation order (ascending i, then ascending j).
  5. Inputs are NOT mutated.
  6. Standard library only; no randomness, network, or external services.
"""


def multiply_polynomials(a, b):
    """
    Multiply two integer polynomials exactly using direct coefficient convolution.

    Args:
        a: list[int] coefficients, index = power of x
        b: list[int] coefficients, index = power of x

    Returns:
        list[int] of length len(a) + len(b) - 1  (exact, untrimmed)
    """
    if not a or not b:
        return []

    # Read-only snapshot; we never write back to a or b.
    A = list(a)
    B = list(b)

    n = len(A) + len(B) - 1
    result = [0] * n

    # Fixed, deterministic accumulation order.
    for i in range(len(A)):
        ai = A[i]
        if ai == 0:
            continue
        for j in range(len(B)):
            bj = B[j]
            if bj == 0:
                continue
            result[i + j] += ai * bj

    return result  # length is exactly len(a) + len(b) - 1


def format_polynomial(coeffs):
    """Read-only pretty-printer for a coefficient array (no mutation)."""
    terms = []
    for power, c in enumerate(coeffs):
        if c == 0:
            continue
        if power == 0:
            terms.append(f"{c}")
        elif power == 1:
            if c == 1:
                terms.append("x")
            elif c == -1:
                terms.append("-x")
            else:
                terms.append(f"{c}x")
        else:
            if c == 1:
                terms.append(f"x^{power}")
            elif c == -1:
                terms.append(f"-x^{power}")
            else:
                terms.append(f"{c}x^{power}")

    if not terms:
        return "0"

    out = terms[0]
    for t in terms[1:]:
        out += (" - " + t[1:]) if t.startswith("-") else (" + " + t)
    return out


# ============================ Tests ============================
if __name__ == "__main__":
    # --- Bug-report regression: top coefficient cancels to zero ---
    A = [1, 0]
    B = [2, 3]
    before_A, before_B = A[:], B[:]

    result = multiply_polynomials(A, B)
    assert result == [2, 3, 0], result
    assert len(result) == len(A) + len(B) - 1
    assert A == before_A and B == before_B
    print("Regression OK:", result)

    # --- Full test battery ---
    test_cases = [
        # (a, b, expected)
        ([1, 2, 3], [4, 5, 6], [4, 13, 28, 27, 18]),
        ([1, 1], [1, -1], [1, 0, -1]),
        ([2], [3], [6]),
        ([1, 0, 1], [1, 0, 1], [1, 0, 2, 0, 1]),        # (1 + x^2)^2
        ([-1, -2], [-3, -4], [3, 10, 8]),
        ([0], [1, 2, 3], [0, 0, 0]),                     # zero polynomial
        ([1, 2, 3], [0], [0, 0, 0]),
        ([1, -2, 1], [1, -2, 1], [1, -4, 6, -4, 1]),     # (x - 1)^4
        ([1, 0], [2, 3], [2, 3, 0]),                     # leading zero preserved
        ([0, 0, 1], [1, 1], [0, 0, 1, 1]),
        ([], [1, 2], []),                                # empty input
        ([1, 2], [], []),
    ]

    all_passed = True
    for idx, (a, b, expected) in enumerate(test_cases, 1):
        got = multiply_polynomials(a, b)
        ok = got == expected
        all_passed &= ok
        print(f"Test {idx:2d}: {'PASS' if ok else 'FAIL'}  "
              f"{format_polynomial(a)} * {format_polynomial(b)} "
              f"= {format_polynomial(got)}  -> {got}")
        if not ok:
            print(f"          expected: {expected}")

    print("\nAll tests passed!" if all_passed else "\nSome tests FAILED.")