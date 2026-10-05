"""
Edit Distance With Transposition (Damerau-Levenshtein, unrestricted).

Operations (each cost 1):
    - insertion
    - deletion
    - substitution
    - transposition of two ADJACENT characters

Uses dynamic programming with an explicit transposition transition
(Lowrance-Wagner), which permits a transposed character to participate
in further edits. Deterministic: min over a fixed, ordered list of
integer candidates.

Standard library only. No randomness, network, APIs, or interaction.
"""


def edit_distance(s1: str, s2: str) -> int:
    """
    Return the unrestricted Damerau-Levenshtein distance between s1 and s2.
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

            # Explicit transposition transition (unrestricted):
            # reach back to last occurrences i1, j1; pay skipped deletions
            # and insertions plus 1 for the swap itself.
            if i1 > 0 and j1 > 0:
                candidates.append(
                    dp[i1 - 1][j1 - 1]
                    + (i - i1 - 1)   # deletions between i1 and i
                    + 1              # the transposition
                    + (j - j1 - 1)   # insertions between j1 and j
                )

            dp[i][j] = min(candidates)

            if s1[i - 1] == s2[j - 1]:
                db = j

        da[s1[i - 1]] = i

    return dp[n][m]


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
        result = edit_distance(s1, s2)
        ok = (result == expected)
        all_ok &= ok
        status = "OK " if ok else "FAIL"
        print(f"[{status}] distance({s1!r}, {s2!r}) = {result} (expected {expected})")

    print()
    print("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED")