from typing import Union, Dict, Any


def damerau_levenshtein(
    s1: str,
    s2: str,
    return_summary: bool = False,
) -> Union[int, Dict[str, Any]]:
    """
    Compute the Damerau-Levenshtein distance between s1 and s2.

    Operations (each cost 1): insertion, deletion, substitution,
    and adjacent transposition.

    Parameters
    ----------
    s1, s2 : str
        Input strings.
    return_summary : bool, default False
        If False (default), returns an int (original behavior, unchanged).
        If True, returns a dict with 'distance' and 'operation_summary'.

    Returns
    -------
    int
        If return_summary is False.
    dict
        If return_summary is True: {'distance': int, 'operation_summary': int}.
    """
    n, m = len(s1), len(s2)

    # DP table: d[i][j] = edit distance between s1[:i] and s2[:j]
    d = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j

    # Counters for operation_summary
    cell_evaluations = 0
    transposition_checks = 0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # --- major computational decision #1: evaluate this cell ---
            cell_evaluations += 1

            cost_sub = 0 if s1[i - 1] == s2[j - 1] else 1

            d[i][j] = min(
                d[i - 1][j] + 1,             # deletion
                d[i][j - 1] + 1,             # insertion
                d[i - 1][j - 1] + cost_sub,  # match / substitution
            )

            # --- major computational decision #2: transposition precondition test ---
            if i > 1 and j > 1:
                transposition_checks += 1
                if (s1[i - 1] == s2[j - 2]
                        and s1[i - 2] == s2[j - 1]):
                    d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)

    distance = d[n][m]

    if not return_summary:
        return distance

    return {
        "distance": distance,
        "operation_summary": cell_evaluations + transposition_checks,
    }


if __name__ == "__main__":
    # Original behavior preserved (returns int)
    print(damerau_levenshtein("teh", "the"))            # 1
    print(damerau_levenshtein("kitten", "sitting"))     # 3
    print(damerau_levenshtein("", "abc"))               # 3

    # New feature enabled
    result = damerau_levenshtein("teh", "the", return_summary=True)
    print(result)
    # n=3, m=3 -> cells = 9
    # transposition checks: i>1 and j>1 -> (2,2),(2,3),(3,2),(3,3) = 4
    # operation_summary = 9 + 4 = 13
    # expected: {'distance': 1, 'operation_summary': 13}

    # Regression tests: original outputs must be unchanged
    tests = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("abc", "abd", 1),
        ("abc", "ab", 1),
        ("ab", "abc", 1),
        ("ab", "ba", 1),
        ("ca", "abc", 3),
        ("kitten", "sitting", 3),
        ("teh", "the", 1),
        ("a cat", "an act", 3),
    ]

    ok = True
    for a, b, expected in tests:
        got = damerau_levenshtein(a, b)  # original call signature
        status = "OK " if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"[{status}] d({a!r}, {b!r}) = {got}  (expected {expected})")

    print("\nAll original tests passed." if ok else "\nSome original tests failed.")

    # Summary feature tests
    a, b = "teh", "the"
    r = damerau_levenshtein(a, b, return_summary=True)
    expected_summary = len(a) * len(b) + max(0, (len(a) - 1)) * max(0, (len(b) - 1))
    assert r == {"distance": 1, "operation_summary": expected_summary}, r
    print("Summary feature OK:", r)