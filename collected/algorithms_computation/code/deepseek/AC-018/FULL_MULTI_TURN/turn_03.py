"""
Exact Polynomial Product
========================
Multiply two integer polynomials exactly via direct coefficient convolution.

Original required outputs (unchanged):
  - exact integer coefficient list of length len(a) + len(b) - 1
  - no trimming, interior zeros preserved
  - negative coefficients supported
  - deterministic accumulation order (ascending i, then ascending j)
  - inputs not mutated
  - empty input -> []

New opt-in feature:
  - return_operations=True attaches an `operation_summary` dict that counts
    major computational decisions/operations performed by the algorithm.
  - When the flag is False (default), the return value is exactly the original
    coefficient list, with no other changes.
"""

from typing import Any


def multiply_polynomials(a, b, *, return_operations: bool = False) -> Any:
    """
    Multiply two integer polynomials exactly using direct coefficient convolution.

    Args:
        a: list[int] coefficients, index = power of x
        b: list[int] coefficients, index = power of x
        return_operations: if True, return (coeffs, operation_summary_dict);
                           if False, return coeffs only (original behavior).

    Returns:
        list[int]                          if return_operations is False
        (list[int], dict)                  if return_operations is True
    """
    # ---- Empty-input path: preserve original contract exactly ----
    if not a or not b:
        if not return_operations:
            return []
        # Deterministic summary for the empty case.
        summary = {
            "input_lengths": (len(a), len(b)),
            "accumulation_slots": 0,
            "pairs_examined": 0,
            "multiplications": 0,
            "additions": 0,
            "total_decisions": 0,
        }
        return [], summary

    # Read-only snapshot; inputs must not be mutated.
    A = list(a)
    B = list(b)

    n = len(A) + len(B) - 1
    result = [0] * n

    # ---- Deterministic counters (only tracked if the feature is requested) ----
    pairs_examined = 0
    multiplications = 0
    additions = 0

    # Fixed, deterministic accumulation order.
    for i in range(len(A)):
        ai = A[i]
        for j in range(len(B)):
            pairs_examined += 1
            bj = B[j]
            if ai == 0 or bj == 0:
                continue
            result[i + j] += ai * bj
            multiplications += 1
            additions += 1

    if not return_operations:
        return result  # exactly the original output

    operation_summary = {
        "input_lengths": (len(A), len(B)),
        "accumulation_slots": n,
        "pairs_examined": pairs_examined,
        "multiplications": multiplications,
        "additions": additions,
        "total_decisions": pairs_examined + multiplications + additions,
    }
    return result, operation_summary


def format_polynomial(coeffs):
    """Read-only pretty-printer for a coefficient array."""
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

    # --- Original behavior must be unchanged when feature is off ---
    assert multiply_polynomials([1, 2, 3], [4, 5, 6]) == [4, 13, 28, 27, 18]
    assert multiply_polynomials([1, 1], [1, -1]) == [1, 0, -1]
    assert multiply_polynomials([], [1, 2]) == []
    assert multiply_polynomials([1, 2], []) == []
    assert multiply_polynomials([0], [1, 2, 3]) == [0, 0, 0]
    assert multiply_polynomials([1, 0], [2, 3]) == [2, 3, 0]  # no trimming
    print("Original contract (feature off): PASS")

    # --- Inputs must not be mutated in either mode ---
    A, B = [1, 0, 1], [1, -1]
    A0, B0 = A[:], B[:]
    _ = multiply_polynomials(A, B)
    _ = multiply_polynomials(A, B, return_operations=True)
    assert A == A0 and B == B0
    print("No mutation of inputs: PASS")

    # --- New feature: operation_summary present and deterministic ---
    coeffs, summary = multiply_polynomials([1, 2, 3], [4, 5, 6],
                                           return_operations=True)
    assert coeffs == [4, 13, 28, 27, 18]  # original output unchanged
    assert summary == {
        "input_lengths": (3, 3),
        "accumulation_slots": 5,
        "pairs_examined": 9,
        "multiplications": 9,
        "additions": 9,
        "total_decisions": 27,
    }, summary
    print("Feature on, dense case: PASS ->", summary)

    # --- Feature on, zero-skipping path counted ---
    coeffs, summary = multiply_polynomials([1, 0], [2, 3],
                                           return_operations=True)
    assert coeffs == [2, 3, 0]
    assert summary == {
        "input_lengths": (2, 2),
        "accumulation_slots": 3,
        "pairs_examined": 4,      # every (i, j) visited
        "multiplications": 2,     # only 1*2 and 1*3 (0*b skipped)
        "additions": 2,
        "total_decisions": 8,
    }, summary
    print("Feature on, sparse path: PASS ->", summary)

    # --- Feature on, empty input ---
    coeffs, summary = multiply_polynomials([], [1, 2], return_operations=True)
    assert coeffs == []
    assert summary["total_decisions"] == 0
    print("Feature on, empty input: PASS ->", summary)

    # --- Determinism: same call yields identical summary each time ---
    s1 = multiply_polynomials([1, -2, 1], [1, -2, 1], return_operations=True)[1]
    s2 = multiply_polynomials([1, -2, 1], [1, -2, 1], return_operations=True)[1]
    assert s1 == s2
    print("Deterministic summary: PASS")

    print("\nAll tests passed.")