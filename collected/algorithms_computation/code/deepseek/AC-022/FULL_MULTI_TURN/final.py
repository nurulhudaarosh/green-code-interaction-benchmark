"""
Edit Distance With Transposition (Damerau-Levenshtein, unrestricted).

Operations (each cost 1): insertion, deletion, substitution,
and transposition of two ADJACENT characters.

Dynamic programming with an explicit transposition transition
(Lowrance-Wagner), permitting a transposed character to participate
in further edits.

Deterministic tie handling:
    - Candidates are collected in a fixed, ordered list:
        [deletion, insertion, match/substitution] (+ transposition last).
    - min() is applied to that fixed list of ints.
    - da/db record the MOST RECENT occurrences so repeated values are
      handled correctly regardless of dict iteration order.
    - No randomness, no sets, no reliance on dict ordering.

Optional feature: return_summary=True returns a dict with the original
distance under "distance" plus a deterministic "operation_summary".

When the feature is disabled or not requested, the function returns
exactly an int, identical to the original behavior.

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

    Default (return_summary=False): returns an int.
    return_summary=True: returns
        {
            "distance": int,
            "operation_summary": {
                "decisions": int,
                "cells_filled": int,
                "transposition_branches": int,
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

    # da[c] = MOST RECENT 1-based index in s1 where character c was seen.
    # Sentinel 0 means "never seen". Repeated values overwrite older entries.
    da: Dict[str, int] = {}
    for c in s1:
        da[c] = 0

    cells_filled = 0
    transposition_branches = 0

    for i in range(1, n + 1):
        # db = MOST RECENT j where s2[j-1] == s1[i-1] in this row.
        db = 0
        for j in range(1, m + 1):
            i1 = da.get(s2[j - 1], 0)  # last i where s1[i-1] == s2[j-1]
            j1 = db                    # last j where s2[j-1] == s1[i-1]

            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            # Fixed, ordered candidate list -> deterministic tie handling.
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
            cells_filled += 1

            # Update db on EVERY match so repeated values are handled.
            if s1[i - 1] == s2[j - 1]:
                db = j

        # Overwrite da with the latest position of s1[i-1] (repeated values).
        da[s1[i - 1]] = i

    distance = dp[n][m]

    if not return_summary:
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
    # (s1, s2, expected_distance, label)
    tests = [
        # --- Original cases (must remain unchanged) ---
        ("", "", 0, "both empty"),
        ("", "abc", 3, "empty source"),
        ("abc", "", 3, "empty target"),
        ("abc", "abc", 0, "identical"),
        ("abc", "abd", 1, "one substitution"),
        ("abc", "ab", 1, "one deletion"),
        ("ab", "abc", 1, "one insertion"),
        ("ab", "ba", 1, "single adjacent transposition"),
        ("teh", "the", 1, "classic transposition"),
        ("kitten", "sitting", 3, "classic Levenshtein example"),
        ("CA", "ABC", 2, "OSA=3, true DL=2"),
        ("ca", "abc", 3, "unrestricted DL divergence"),
        ("abcd", "badc", 2, "two independent transpositions"),
        ("abcdef", "abcfed", 1, "one swap at the end"),
        ("a cat", "an act", 2, "mixed edits"),
        ("intention", "execution", 5, "long mixed example"),

        # --- Difficult case: repeated values ---
        ("aa", "aa", 0, "repeated identical"),
        ("aaaa", "aaaa", 0, "long repeated identical"),
        ("aaaa", "aaa", 1, "repeated with one deletion"),
        ("aaa", "aaaa", 1, "repeated with one insertion"),
        ("aaaa", "bbbb", 4, "repeated, full substitution"),
        ("aabb", "bbaa", 2, "repeated block swap"),
        ("abab", "baba", 2, "alternating repeated"),
        ("abcabc", "acbacb", 3, "repeated pattern with swaps"),
        ("mississippi", "misisisippi", 2, "repeated letters in a word"),
        ("banana", "anaban", 3, "repeated letters multiple swaps"),
        ("aab", "baa", 2, "repeated a's around a swap"),
        ("ca", "abc", 3, "repeated 'a' forces da/db updates"),

        # --- Difficult case: ties (equal-cost candidates) ---
        # For identical strings every cell has deletion=insertion=substitution+0;
        # the minimum must deterministically be the diagonal (cost 0 path).
        ("abc", "abc", 0, "tie: all candidates equal, diagonal wins"),
        ("xyz", "xyz", 0, "tie with distinct chars"),
        # Homogeneous strings make deletion/insertion tie repeatedly.
        ("aaaa", "aa", 2, "tie: deletions vs insertions"),
        ("aa", "aaaa", 2, "tie: insertions vs deletions"),
        # One substitution vs one deletion+insertion tie at some cells;
        # correct minimum is still 1 via diagonal substitution.
        ("ab", "ac", 1, "tie broken by substitution candidate"),
        # Transposition and two substitutions may tie; min is deterministic.
        ("ab", "ba", 1, "transposition beats 2 substitutions"),
    ]

    print("=== Distance checks (default behavior, must return int) ===")
    all_ok = True
    for s1, s2, expected, label in tests:
        result = edit_distance(s1, s2)
        ok = (result == expected) and isinstance(result, int)
        all_ok &= ok
        status = "OK " if ok else "FAIL"
        print(f"[{status}] {label:45s} distance({s1!r}, {s2!r}) = {result} (expected {expected})")

    print()
    print("=== Determinism check: same input repeated 5x ===")
    det_ok = True
    for s1, s2, expected, label in tests:
        results = [edit_distance(s1, s2) for _ in range(5)]
        if len(set(results)) != 1 or results[0] != expected:
            det_ok = False
            print(f"[FAIL] non-deterministic for {label}: {results}")
    all_ok &= det_ok
    if det_ok:
        print("[OK ] all inputs produced identical results across 5 runs")

    print()
    print("=== operation_summary determinism (feature enabled) ===")
    summary_ok = True
    sample = [
        ("", "", 0),
        ("aaaa", "aaaa", 0),
        ("CA", "ABC", 2),
        ("abab", "baba", 2),
        ("mississippi", "misisisippi", 2),
    ]
    for s1, s2, expected in sample:
        outs = [edit_distance(s1, s2, return_summary=True) for _ in range(3)]
        first = outs[0]
        consistent = all(o == first for o in outs)
        distance_ok = first["distance"] == expected
        fields_ok = set(first.keys()) == {"distance", "operation_summary"}
        sub_fields_ok = set(first["operation_summary"].keys()) == {
            "decisions", "cells_filled", "transposition_branches"
        }
        ok = consistent and distance_ok and fields_ok and sub_fields_ok
        summary_ok &= ok
        status = "OK " if ok else "FAIL"
        print(
            f"[{status}] distance({s1!r}, {s2!r}) = {first['distance']} "
            f"| summary={first['operation_summary']}"
        )
    all_ok &= summary_ok

    print()
    print("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED")