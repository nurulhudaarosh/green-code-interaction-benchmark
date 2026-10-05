"""
Exact Polynomial Product
========================
Multiply two integer polynomials exactly via direct coefficient convolution.

Preserved original rules:
  - exact integer coefficients, length len(a) + len(b) - 1
  - no trimming, interior zeros kept
  - negative coefficients supported
  - deterministic tie handling: ascending i, then ascending j
  - inputs never mutated
  - empty input -> []
  - standard library only, deterministic, no randomness/network

Optional:
  - return_operations=True attaches a deterministic `operation_summary`.
"""

from typing import Any


def multiply_polynomials(a, b, *, return_operations: bool = False) -> Any:
    """Exact integer polynomial multiplication via direct coefficient convolution."""
    # Empty input: preserve original contract exactly.
    if not a or not b:
        if not return_operations:
            return []
        return [], {
            "input_lengths": (len(a), len(b)),
            "accumulation_slots": 0,
            "pairs_examined": 0,
            "multiplications": 0,
            "additions": 0,
            "total_decisions": 0,
        }

    # Read-only snapshot — inputs are never mutated.
    A = list(a)
    B = list(b)

    n = len(A) + len(B) - 1
    result = [0] * n

    pairs_examined = 0
    multiplications = 0
    additions = 0

    # Deterministic tie order: ascending i, then ascending j.
    for i in range(len(A)):
        ai = A[i]
        for j in range(len(B)):
            pairs_examined += 1
            bj = B[j]
            if ai == 0 or bj == 0:
                continue
            result[i + j] += ai * bj   # repeated values summed exactly, in fixed order
            multiplications += 1
            additions += 1

    if not return_operations:
        return result  # exactly the original output

    return result, {
        "input_lengths": (len(A), len(B)),
        "accumulation_slots": n,
        "pairs_examined": pairs_examined,
        "multiplications": multiplications,
        "additions": additions,
        "total_decisions": pairs_examined + multiplications + additions,
    }


def format_polynomial(coeffs):
    """Read-only pretty-printer."""
    terms = []
    for power, c in enumerate(coeffs):
        if c == 0:
            continue
        if power == 0:
            terms.append(f"{c}")
        elif power == 1:
            terms.append("x" if c == 1 else "-x" if c == -1 else f"{c}x")
        else:
            terms.append(
                f"x^{power}" if c == 1 else
                f"-x^{power}" if c == -1 else
                f"{c}x^{power}"
            )
    if not terms:
        return "0"
    out = terms[0]
    for t in terms[1:]:
        out += (" - " + t[1:]) if t.startswith("-") else (" + " + t)
    return out


# ============================ Tests ============================
if __name__ == "__main__":

    # ---------- Original contract (must not change) ----------
    original_cases = [
        ([1, 2, 3], [4, 5, 6], [4, 13, 28, 27, 18]),
        ([1, 1], [1, -1], [1, 0, -1]),
        ([2], [3], [6]),
        ([1, 0, 1], [1, 0, 1], [1, 0, 2, 0, 1]),
        ([-1, -2], [-3, -4], [3, 10, 8]),
        ([0], [1, 2, 3], [0, 0, 0]),
        ([1, 2, 3], [0], [0, 0, 0]),
        ([1, 0], [2, 3], [2, 3, 0]),      # no trimming of top zero
        ([], [1, 2], []),
        ([1, 2], [], []),
    ]
    for idx, (a, b, exp) in enumerate(original_cases, 1):
        got = multiply_polynomials(a, b)
        assert got == exp, (idx, a, b, got, exp)
    print("Original contract: PASS")

    # ---------- Difficult case A: repeated values ----------
    # A1: same value repeated inside one input.
    assert multiply_polynomials([1, 1], [1, 1]) == [1, 2, 1]
    # A2: value 2 repeated three times on each side -> (2 + 2x + 2x^2)^2
    #     = 4 + 8x + 12x^2 + 8x^3 + 4x^4
    assert multiply_polynomials([2, 2, 2], [2, 2, 2]) == [4, 8, 12, 8, 4]
    # A3: repeated negative value
    assert multiply_polynomials([-3, -3], [-3, -3]) == [9, 18, 9]
    # A4: repeated value + interior zero, must not be trimmed or deduped
    assert multiply_polynomials([5, 5, 5], [1, 0, 1]) == [5, 5, 10, 5, 5]
    print("Difficult case A (repeated values): PASS")

    # ---------- Difficult case B: deterministic ties ----------
    # B1: many pairs collide at the same output index.
    #     (1 + x + x^2 + x^3) * (1 + x + x^2 + x^3)
    #     Each middle index gets multiple contributions from different (i, j).
    a = [1, 1, 1, 1]
    b = [1, 1, 1, 1]
    expected = [1, 2, 3, 4, 3, 2, 1]
    assert multiply_polynomials(a, b) == expected

    # B2: repeated runs of the same value -> many exact ties at each k.
    #     (1 + 2x + 3x^2)^2 = 1 + 4x + 10x^2 + 12x^3 + 9x^4
    assert multiply_polynomials([1, 2, 3], [1, 2, 3]) == [1, 4, 10, 12, 9]

    # B3: determinism — same inputs give identical coefficients AND identical
    #     operation_summary on every call.
    runs = [
        multiply_polynomials([3, -1, 4, -1, 5], [2, 7, -1, 7, 2],
                             return_operations=True)
        for _ in range(5)
    ]
    coeffs_first, summary_first = runs[0]
    for coeffs_r, summary_r in runs[1:]:
        assert coeffs_r == coeffs_first
        assert summary_r == summary_first
    print("Difficult case B (deterministic ties): PASS")
    print("  sample coeffs :", coeffs_first)
    print("  sample summary:", summary_first)

    # ---------- Tie handling must not depend on input length order ----------
    # Swapping operands must give the same coefficient array (commutativity),
    # because both use ascending i / ascending j and integer ops.
    A, B = [1, -2, 3, -4], [5, 6, -7, 8, -9]
    assert multiply_polynomials(A, B) == multiply_polynomials(B, A)
    print("Commutativity under fixed tie order: PASS")

    # ---------- Inputs must never be mutated ----------
    A, B = [1, 0, 2, 0, 3], [-1, 0, -1]
    A0, B0 = A[:], B[:]
    _ = multiply_polynomials(A, B)
    _ = multiply_polynomials(A, B, return_operations=True)
    assert A == A0 and B == B0
    print("No mutation of inputs: PASS")

    # ---------- Feature off => original output only ----------
    out = multiply_polynomials([1, 1, 1], [1, 1, 1])
    assert isinstance(out, list) and out == [1, 2, 3, 2, 1]
    print("Feature off returns bare list: PASS")

    # ---------- Feature on => original output preserved + summary added ----------
    coeffs, summary = multiply_polynomials([1, 1, 1], [1, 1, 1],
                                           return_operations=True)
    assert coeffs == [1, 2, 3, 2, 1]              # unchanged
    assert summary["accumulation_slots"] == 5
    assert summary["pairs_examined"] == 9
    assert summary["multiplications"] == 9
    assert summary["additions"] == 9
    assert summary["total_decisions"] == 27
    print("Feature on preserves output + adds summary: PASS")

    print("\nAll tests passed.")