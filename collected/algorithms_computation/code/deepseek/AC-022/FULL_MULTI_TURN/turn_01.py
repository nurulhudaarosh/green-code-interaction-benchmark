def edit_distance(s1: str, s2: str) -> int:
    """
    Compute Damerau-Levenshtein (optimal string alignment) distance between s1 and s2.
    Allowed operations (each cost 1): insertion, deletion, substitution,
    and transposition of two adjacent characters.

    Returns the minimum edit distance as a non-negative integer.
    """
    n, m = len(s1), len(s2)

    # dp[i][j] = distance between s1[:i] and s2[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    # Fill the table
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            best = min(
                dp[i - 1][j] + 1,        # deletion
                dp[i][j - 1] + 1,        # insertion
                dp[i - 1][j - 1] + cost  # match or substitution
            )

            # Adjacent transposition
            if (i >= 2 and j >= 2
                    and s1[i - 1] == s2[j - 2]
                    and s1[i - 2] == s2[j - 1]):
                best = min(best, dp[i - 2][j - 2] + 1)

            dp[i][j] = best

    return dp[n][m]


if __name__ == "__main__":
    # Deterministic test cases
    tests = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("abc", "abd", 1),          # substitution
        ("abc", "ab", 1),           # deletion
        ("ab", "abc", 1),           # insertion
        ("ab", "ba", 1),            # transposition
        ("ca", "abc", 2),           # insertion + transposition
        ("kitten", "sitting", 3),   # classic Levenshtein example
        ("teh", "the", 1),          # single transposition
        ("a cat", "an act", 2),     # multiple operations
        ("abcdef", "abcfed", 1),    # one adjacent swap at the end
        ("abcd", "badc", 2),        # two independent transpositions
    ]

    for s1, s2, expected in tests:
        result = edit_distance(s1, s2)
        status = "OK " if result == expected else "FAIL"
        print(f"[{status}] distance({s1!r}, {s2!r}) = {result} (expected {expected})")