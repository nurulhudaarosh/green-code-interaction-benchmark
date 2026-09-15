from typing import Tuple


def lcs(x: str, y: str) -> Tuple[int, str]:
    """
    Compute the Longest Common Subsequence (LCS) of two strings.

    Tie-breaking rule:
        When dp[i-1][j] == dp[i][j-1], reconstruction prefers
        advancing in the first string x (moving from (i, j)
        to (i-1, j)).

    Returns:
        (lcs_length, lcs_string)
    """

    n = len(x)
    m = len(y)

    # DP table.
    # dp[i][j] = LCS length of x[:i] and y[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Predecessor table.
    # Values:
    #   "diag" -> matched characters, move (i-1, j-1)
    #   "up"   -> advance in first string, move (i-1, j)
    #   "left" -> advance in second string, move (i, j-1)
    pred = [[None] * (m + 1) for _ in range(n + 1)]

    # Fill DP table.
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                pred[i][j] = "diag"

            elif dp[i - 1][j] >= dp[i][j - 1]:
                # On a tie, prefer advancing in the first string.
                dp[i][j] = dp[i - 1][j]
                pred[i][j] = "up"

            else:
                dp[i][j] = dp[i][j - 1]
                pred[i][j] = "left"

    # Reconstruct one LCS using predecessors.
    result = []
    i, j = n, m

    while i > 0 and j > 0:
        if pred[i][j] == "diag":
            result.append(x[i - 1])
            i -= 1
            j -= 1

        elif pred[i][j] == "up":
            i -= 1

        elif pred[i][j] == "left":
            j -= 1

        else:
            break

    # Reconstruction happens backwards.
    result.reverse()

    return dp[n][m], "".join(result)


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def run_tests() -> None:
    test_cases = [
        ("ABCBDAB", "BDCABA"),
        ("AGGTAB", "GXTXAYB"),
        ("", "ABC"),
        ("ABC", ""),
        ("ABC", "ABC"),
        ("ABC", "DEF"),
        ("AAAA", "AA"),
        ("ABCD", "ACBD"),
    ]

    for x, y in test_cases:
        length, subsequence = lcs(x, y)

        # Basic correctness checks.
        assert length == len(subsequence)

        # Verify that the result is a subsequence of both strings.
        def is_subsequence(s: str, t: str) -> bool:
            it = iter(t)
            return all(char in it for char in s)

        assert is_subsequence(subsequence, x)
        assert is_subsequence(subsequence, y)

        print(f"x = {x!r}, y = {y!r}")
        print(f"LCS length = {length}")
        print(f"LCS = {subsequence!r}")
        print()


if __name__ == "__main__":
    run_tests()