def damerau_levenshtein(a: str, b: str) -> int:
    """
    Compute edit distance with insertion, deletion, substitution,
    and adjacent transposition, each costing 1.
    """
    n, m = len(a), len(b)

    # dp[i][j] = distance between a[:i] and b[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    # Fill the table
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost_sub = 0 if a[i - 1] == b[j - 1] else 1

            dp[i][j] = min(
                dp[i - 1][j] + 1,               # deletion
                dp[i][j - 1] + 1,               # insertion
                dp[i - 1][j - 1] + cost_sub,    # substitution or match
            )

            # Adjacent transposition
            if (i > 1 and j > 1
                    and a[i - 1] == b[j - 2]
                    and a[i - 2] == b[j - 1]):
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)

    return dp[n][m]


if __name__ == "__main__":
    tests = [
        ("", "", 0),
        ("abc", "", 3),
        ("", "abc", 3),
        ("abc", "abc", 0),
        ("abc", "abd", 1),
        ("abc", "acb", 1),        # one transposition
        ("ca", "abc", 3),
        ("kitten", "sitting", 3),
        ("ab", "ba", 1),          # transposition
        ("abcd", "badc", 2),      # two transpositions
        ("a cat", "an act", 3),
    ]

    for a, b, expected in tests:
        got = damerau_levenshtein(a, b)
        status = "OK " if got == expected else "FAIL"
        print(f"[{status}] d({a!r}, {b!r}) = {got} (expected {expected})")