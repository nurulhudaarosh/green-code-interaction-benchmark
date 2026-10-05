def damerau_levenshtein(a: str, b: str) -> int:
    """
    Compute edit distance with insertion, deletion, substitution,
    and adjacent transposition, each costing 1.

    Deterministic. Standard library only.
    """
    n, m = len(a), len(b)

    # dp[i][j] = edit distance between a[:i] and b[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    # Fill table
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1

            dp[i][j] = min(
                dp[i - 1][j] + 1,        # deletion
                dp[i][j - 1] + 1,        # insertion
                dp[i - 1][j - 1] + cost  # match or substitution
            )

            # Adjacent transposition
            if (i >= 2 and j >= 2
                    and a[i - 1] == b[j - 2]
                    and a[i - 2] == b[j - 1]):
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)

    return dp[n][m]


if __name__ == "__main__":
    # Deterministic self-tests
    tests = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("abc", "abd", 1),          # substitution
        ("abc", "ab", 1),           # deletion
        ("ab", "abc", 1),           # insertion
        ("ab", "ba", 1),            # transposition
        ("ca", "abc", 3),
        ("abcd", "abdc", 1),        # transposition in middle
        ("kitten", "sitting", 3),
        ("Saturday", "Sunday", 3),
        ("a cat", "an act", 2),     # transposition + insertion
    ]

    for s1, s2, expected in tests:
        got = damerau_levenshtein(s1, s2)
        status = "OK" if got == expected else "FAIL"
        print(f"[{status}] d({s1!r}, {s2!r}) = {got} (expected {expected})")