def damerau_levenshtein(s1: str, s2: str) -> int:
    """
    Compute the Damerau-Levenshtein distance between s1 and s2.
    Operations (each cost 1): insertion, deletion, substitution,
    and adjacent transposition.
    """
    n, m = len(s1), len(s2)

    # d[i][j] = edit distance between s1[:i] and s2[:j]
    d = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost_sub = 0 if s1[i - 1] == s2[j - 1] else 1

            d[i][j] = min(
                d[i - 1][j] + 1,            # deletion
                d[i][j - 1] + 1,            # insertion
                d[i - 1][j - 1] + cost_sub, # match / substitution
            )

            # Adjacent transposition
            if (i > 1 and j > 1
                    and s1[i - 1] == s2[j - 2]
                    and s1[i - 2] == s2[j - 1]):
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)

    return d[n][m]


if __name__ == "__main__":
    tests = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("abc", "abd", 1),          # substitution
        ("abc", "ab", 1),           # deletion
        ("ab", "abc", 1),           # insertion
        ("ab", "ba", 1),            # transposition
        ("ca", "abc", 3),           # classic CLRS example
        ("kitten", "sitting", 3),   # without transposition benefit
        ("teh", "the", 1),          # pure transposition
        ("a cat", "an act", 3),
    ]

    ok = True
    for a, b, expected in tests:
        got = damerau_levenshtein(a, b)
        status = "OK " if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"[{status}] d({a!r}, {b!r}) = {got}  (expected {expected})")

    print("\nAll tests passed." if ok else "\nSome tests failed.")