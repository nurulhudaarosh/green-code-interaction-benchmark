"""
Edit Distance With Transposition (Damerau-Levenshtein, unrestricted).

Operations (each cost 1): insertion, deletion, substitution,
and transposition of two ADJACENT characters.

Dynamic programming with an explicit transposition transition
(Lowrance-Wagner), permitting a transposed character to participate
in further edits. Deterministic: min over a fixed, ordered list of
integer candidates.

Optional feature: return_summary=True returns a dict with the
original distance under "distance" plus an "operation_summary"
field reporting deterministic computational counts.

When the feature is disabled or not requested, behavior is identical
to the original: the function returns exactly an int.

Standard library only. No randomness, network, APIs, or interaction.
"""

from typing import Union, Dict, Any


def edit_distance(
    s1: str,
    s2: str,
    return_summary: bool = False,
) -> Union[int, Dict[str, Any]]:
    """
    Return the unrestricted Damerau-Levenshtein distance between s1 and s2.

    If return_summary is False (default), returns an int -- identical
    to the original behavior.

    If return_summary is True, returns a dict:
        {
            "distance": int,
            "operation_summary": {
                "decisions": int,                 # major decisions/operations
                "cells_filled": int,              # n * m DP cells
                "transposition_branches": int,    # cells where transposition fired
            },
        }
    """
    n, m = len(s1), len(s2)

    # dp[i][j] = distance between s1[:i] and s2[:j], 1-based over strings.
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    # da[c] = largest 1-based index in s1 where character c was seen.
    da = {}
    for c in s1:
        da[c] = 0

    # --- summary counters (deterministic) ---
    cells_filled = 0
    transposition_branches = 0

    for i in range(1, n + 1):
        db = 0  # last j where s2[j-1] == s1[i-1]
        for j in range(1, m + 1):
            i1 = da.get(s2[j - 1], 0)  # last i where s1[i-1] == s2[j-1]
            j1 = db                    # last j where s2[j-1] == s1[i-1]

            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            candidates = [
                dp[i - 1][j] + 1,          # deletion
                dp[i][j - 1] + 1,          # insertion
                dp[i - 1][j - 1] + cost,   # match / substitution
            ]

            # Explicit transposition transition (unrestricted).
            if i1 > 0 and j1 > 0:
                candidates.append(
                    dp[i1 - 1][j1 - 1]
                    + (i - i1 - 1)   # deletions between i1 and i
                    + 1              # the transposition
                    + (j - j1 - 1)   # insertions between j1 and j
                )
                transposition_branches += 1

            dp[i][j] = min(candidates)

            # One "major computational decision" per filled cell.
            cells_filled += 1

            if s1[i - 1] == s2[j - 1]:
                db = j

        da[s1[i - 1]] = i

    distance = dp[n][m]

    if not return_summary:
        # Original behavior: exactly an int, unchanged.
        return distance

    return {
        "distance": distance,
        "operation_summary": {
            "decisions": cells_filled + transposition_branches,
            "cells_filled": cells_filled,
            "transposition_branches": transposition_branches,
        },
    }


if __name__ == "__main__":
    tests = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("abc", "abd", 1),
        ("abc", "ab", 1),
        ("ab", "abc", 1),
        ("ab", "ba", 1),                # single adjacent transposition
        ("teh", "the", 1),              # classic transposition
        ("kitten", "sitting", 3),
        ("CA", "ABC", 2),               # OSA gives 3; true DL gives 2
        ("ca", "abc", 3),
        ("abcd", "badc", 2),
        ("abcdef", "abcfed", 1),
        ("a cat", "an act", 2),
        ("intention", "execution", 5),
    ]

    all_ok = True
    for s1, s2, expected in tests:
        result = edit_distance(s1, s2)          # default: unchanged behavior
        ok = (result == expected) and isinstance(result, int)
        all_ok &= ok
        status = "OK " if ok else "FAIL"
        print(f"[{status}] distance({s1!r}, {s2!r}) = {result} (expected {expected})")

    print()
    print("--- With return_summary=True (feature enabled) ---")
    for s1, s2, expected in tests[:6] + [("CA", "ABC", 2), ("kitten", "sitting", 3)]:
        out = edit_distance(s1, s2, return_summary=True)
        assert out["distance"] == expected, (s1, s2, out)
        print(
            f"distance({s1!r}, {s2!r}) = {out['distance']} "
            f"| summary = {out['operation_summary']}"
        )

    print()
    print("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED")